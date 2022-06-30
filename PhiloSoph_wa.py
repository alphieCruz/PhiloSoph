
# PHILOSOPH - WEB APPLICATION

# I. IMPORTS

import streamlit as st

from requests import post

from json import loads

from gql import gql, Client

from gql.transport.aiohttp import AIOHTTPTransport

# II. FRONT-END DEFINITION

# II.i. Utilities

reverseProxyAddress = 'https://1a44-2803-1800-11c1-652c-6d47-d289-2517-6dc5.ngrok.io'

def authenticateUser(emailAddress, password):

    def logIn(emailAddress):
        query = 'mutation { getSessionToken(emailAddress : "%s") }'
        sessionToken = loads(post(reverseProxyAddress,
                                  json = {'query' : query % emailAddress}).text)['data']['getSessionToken']
        st.session_state['token'] = sessionToken
        
    query = 'query { verifyCredentials(emailAddress : "%s", password : "%s") }'
    verification = loads(post(reverseProxyAddress,
                              json = {'query' : query % (emailAddress, password)}).text)['data']['verifyCredentials']

    if 'verified' in verification:
        logIn(emailAddress)
        st.session_state['user'] = {'name' : verification[14:],
                                    'email address' : emailAddress}
        if 'authentication problem' in st.session_state:
            del st.session_state['authentication problem']
        st.session_state['ongoing exploration'] = False
    else:
        st.session_state['authentication problem'] = verification

def getClasses():

    query = 'query { getClasses }'
    classes = loads(loads(post(reverseProxyAddress, json = {'query' : query}).text)['data']['getClasses'])
    
    return classes

def terminateExploration():

    st.session_state['ongoing exploration'] = False

clientToTheAPIGateway = Client(transport = AIOHTTPTransport(reverseProxyAddress))

def submitNewWriting():   

    lastKeyUsed = st.session_state['last key used']

    if all([st.session_state[lastKeyUsed + i] for i in range(1, 6)]) and \
       (not st.session_state[lastKeyUsed + 6] or st.session_state[lastKeyUsed + 7]) and \
       (st.session_state[lastKeyUsed + 3] != 'Coponencia' or all([st.session_state[lastKeyUsed + i] for i in range(8, 10)])):

        file = st.session_state[lastKeyUsed + 1]

        query = gql('mutation($writing : Upload!) { storeWriting(writing : $writing) }')
        parameters = {'writing' : file}
        clientToTheAPIGateway.execute(query, variable_values = parameters, upload_files = True)
        
        pendingWritingBaseAttributes = ['class', 'type', 'title', 'abstract', 'authorId', 'fileName', 'instructionCode']
        pendingWritingBaseValues = [*[st.session_state[lastKeyUsed + i] for i in range(2, 6)],
                                    [st.session_state['user']['email address']],
                                    file.name,
                                    1] 
        pendingWriting = dict(zip(pendingWritingBaseAttributes, pendingWritingBaseValues))

        if st.session_state[lastKeyUsed + 6]:
            pendingWriting['authorId'] += st.session_state[lastKeyUsed + 7].split(';')

        if st.session_state[lastKeyUsed + 3] == 'Coponencia':
            pendingWriting['baselineWriting'] = {'title' : st.session_state[lastKeyUsed + 8],
                                                 'authorId' : st.session_state[lastKeyUsed + 9].split(';')}
            numberOfFieldsToClear = 9
        else:
            numberOfFieldsToClear = 7

        query = gql('mutation($pendingWriting : PendingWriting!){ createPendingWriting(pendingWriting : $pendingWriting) }')
        parameters = {'pendingWriting' : pendingWriting}
        clientToTheAPIGateway.execute(query, variable_values = parameters)
        
        key = lastKeyUsed
        for _ in range(numberOfFieldsToClear):
            key += 1
            del st.session_state[key]
        st.session_state['last key used'] = key

        st.session_state['submission'] = 'successful for ' + pendingWriting['title']
        
    else:
        st.session_state['submission'] = 'incomplete' 

def getTypes(chosenClass):

    query = 'query { getTypes(searchClass : "%s") }' % chosenClass
    types = loads(loads(post(reverseProxyAddress, json = {'query' : query}).text)['data']['getTypes'])

    return types

def getWritings(searchClass = None, searchType = None, searchID = None):

    if st.session_state['ongoing exploration']:
        writings = st.session_state['writings under exploration']
    else:
        
        st.session_state['ongoing exploration'] = True
        
        query = gql('query($searchPattern : WritingSearchPattern!) { getWritings(searchPattern : $searchPattern) }')
        searchPattern = dict()
        if searchClass:
            searchPattern['class'] = searchClass
        if searchType:
            searchPattern['type'] = searchType
        if searchID:
            searchPattern['_id'] = searchID
        parameters = {'searchPattern' : searchPattern}
        writings = loads(clientToTheAPIGateway.execute(query, variable_values = parameters)['getWritings'])

        st.session_state['writings under exploration'] = writings

    return writings

def dispatchWriting(fileName):
    query = 'mutation { dispatchWriting(emailAddress : "%s", fileName : "%s") }' % (st.session_state['user']['email address'], fileName)
    post(reverseProxyAddress, json = {'query' : query})

def logOut():
    
    query = 'mutation { removeSessionToken(emailAddress : "%s") }'
    post(reverseProxyAddress, json = {'query' : query % st.session_state['user']['email address']})

    del st.session_state['token']
    del st.session_state['user']

# II.ii Web page

st.title('PhiloSoph')

if 'token' not in st.session_state:

    st.header('Log in')

    if 'authentication problem' in st.session_state:
        if st.session_state['authentication problem'] == 'wrong password':
            st.error('The password does not match the user!')
        else:
            st.error('There is no such user!')            

    emailAddress = st.text_input('Your email address,')
    password = st.text_input('Your password,', type = 'password')
    st.button('Submit!', on_click = authenticateUser, args = (emailAddress, password))

else:

    st.caption(':wave: Hello, %s !' % st.session_state['user']['name'].split(' ')[0])

    st.markdown('##')
    
    st.header('Writings exploration')
    chosenClass = st.selectbox('The class of your interest,', [''] + getClasses(), on_change = terminateExploration)

    st.markdown('*If you wish to create a new class, create a new writing altogether :wink:*')

    with st.expander('Do you wish to create a new writing?'):

        if 'last key used' not in st.session_state:
            st.session_state['last key used'] = 0

        lastKeyUsed = st.session_state['last key used']
        
        st.markdown('#### Your new writing :')
        st.file_uploader('Load a single pdf file.', type = 'pdf', key = lastKeyUsed + 1)
        st.markdown('#### Your new writing\'s information :')
        newWritingClass = st.text_input('It\'s class,', key = lastKeyUsed + 2)
        newWritingType = st.radio('It\'s type,', ['Artículo', 'Ponencia', 'Coponencia'], key = lastKeyUsed + 3)
        st.text_input('It\'s title,', key = lastKeyUsed + 4)
        st.text_area('It\'s abstract,', key = lastKeyUsed + 5)
        otherAuthors = st.checkbox('"I co-authored it with someone else."', key = lastKeyUsed + 6)
        st.text_input('It\'s co-authors (other than yourself) email addresses, separated by a semicolon alone,',
                      placeholder = 'e.g., foo@unal.edu.co;baz@gmail.com;...',
                      disabled = not otherAuthors,
                      key = lastKeyUsed + 7)

        if newWritingType == 'Coponencia':

            st.info('Since your writing is a commentary on someone else\'s writing, we would like you to provide us with some ' + \
                    'of the identitary information of that writing annotated by yours — thus we\'ll be able to verify your claim ' + \
                    'and link both writings for everyone\'s knowing. We thank you in advance :grin:')
            st.markdown('#### Your new writing\'s baseline writing\'s information :')
            st.text_input('The baseline writing\'s title,', key = lastKeyUsed + 8)
            st.text_input('The baseline writing\'s author•s\' email address•es (separate them with a semicolon alone),',
                          placeholder = 'e.g., foo@unal.edu.co, or foo@unal.edu.co;baz@gmail.com;...',
                          key = lastKeyUsed + 9)

        st.button('Submit!', on_click = submitNewWriting)

        if 'submission' in st.session_state:
            if st.session_state['submission'] == 'incomplete':
                st.error('You forgot to fill one or more fields above :confounded: — your submission failed.')
            else:
                writingTitle = st.session_state['submission'][15:]
                st.success('Your submission for "%s" has been succesful! We will notify you on it\'s publishing via email.' % writingTitle)
        
    chosenType = st.selectbox('The type of your interest,', [''] + getTypes(chosenClass), on_change = terminateExploration)

    explore = st.button('Explore!')

    if explore or st.session_state['ongoing exploration']:
        
        writings = getWritings(searchClass = chosenClass, searchType = chosenType)

        buttonId = 'a'

        for writing in writings:

            writingHeader = '#### '
            if not chosenType or not chosenClass:
                introductionHeader = ''
                if not chosenType:
                    if writing['type'] == 'Ponencia':
                        introductionHeader += 'talk '
                    else:
                        introductionHeader += 'paper '
                if not chosenClass:
                    introductionHeader += 'on ' + writing['class']
                introductionHeader = '*' + introductionHeader[0].upper() + introductionHeader[1:] + ' :* '
                writingHeader += introductionHeader
                             
            writingHeader += writing['title']

            st.markdown(writingHeader)
            authorsSentence = writing['authorName'][0]
            for authorName in writing['authorName'][1:]:
                authorsSentence += ' & ' + authorName
            st.markdown('*%s*' % authorsSentence)
            st.write(writing['abstract'])

            _, indentedColumn = st.columns([4, 1])
            indentedColumn.button('Ask for a copy', key = buttonId, on_click = dispatchWriting, args = (writing['fileName'],))
            buttonId += chr(ord(buttonId[-1]) + 1)

            if 'commentaryId' in writing:
                _, indentedColumn = st.columns([1, 22])
                for commentaryId in writing['commentaryId']:
                    commentary = getWritings(searchID = commentaryId)[0]
                    indentedColumn.markdown('##### *Commentary :* %s' % commentary['title'])
                    authorsSentence = commentary['authorName'][0]
                    for authorName in commentary['authorName'][1:]:
                        authorsSentence += ' & ' + authorName
                    indentedColumn.markdown('*%s*' % authorsSentence)
                    indentedColumn.write(commentary['abstract'])

                    indentedColumn.button('Ask for a copy', key = buttonId, on_click = dispatchWriting, args = (commentary['fileName'],))
                    buttonId += chr(ord(buttonId[-1]) + 1)
                    
    st.markdown('# ')
    st.markdown('# ')
    st.markdown('---')
    _, indentedColumn = st.columns([5, 7])
    indentedColumn.button('Log me out', on_click = logOut)
        

        
    

