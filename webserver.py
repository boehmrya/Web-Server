# Authors: Stephen C Phillips, Ryan Boehm

import socket
import select

# Standard socket stuff:
host = '' # do we need socket.gethostname() ?
port = 8000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
backlog = 5
maxsize = 1024
sock.listen(backlog)
inputreq = [sock,]
outputreq = []
            

# Loop forever, listening for requests:
while True:
    inputready,outputready,exceptready = select.select(inputreq, outputreq,[])

    #check each socket that select() said has available data
    for s in inputready: 
        
        #if select returns our server socket, there is a new remote socket trying to connect
        if s == sock: 

            # get client socket and add it to the list of input request
            csock, caddr = sock.accept()
            print ("Connection from: " + str(caddr))
            inputreq.append(csock)
            outputreq.append(csock)

        else:
            # select has indicated that these sockets have data available to recv
            req = s.recv(maxsize) # get the request, 1kB max
            print(req)
            if req:
                # verifiy that the request is valid
                reqList = req.decode().split("\r\n")
                reqList1 = reqList[0].split() # GET, request uri, and HTTP/1.1
                reqList2 = reqList[1].split(":") # host, 127.0.0.1, and port

                # pull out values to check in first list
                reqType = reqList1[0].strip()
                reqURI = reqList1[1].strip()
                reqHTTP = reqList1[2].strip()

                # pull out values to check in second list
                reqHost = reqList2[0].strip()
                reqIP = reqList2[1].strip()
                reqPort = reqList2[2].strip()

                # check all values to ensure that request is valid
                valid = 1
                if reqType != 'GET' and reqType != 'POST':
                    valid = 0
                elif reqURI == '':
                    valid = 0
                elif reqHTTP != 'HTTP/1.1':
                    valid = 0
                elif reqHost != 'Host':
                    valid = 0
                elif reqIP != '127.0.0.1':
                    valid = 0
                elif reqPort != '8000':
                    valid = 0

                # if post, check content type and get the body
                if reqType == 'POST':
                    cType = 0
                    # check content type value
                    for item in reqList:
                        if item == 'Content-Type: application/x-www-form-urlencoded':
                            cType = 1
                    # if we don't have the correct content type, invalidate the post request
                    if cType == 0:
                        valid = 0
                    else:
                        # get body and parse it into a dictionary
                        postBody = reqList[-1]
                        postBodyParts = postBody.split("&")
                        postDict = {} #holds key value pairs
                        # extract key,value pairs from post body
                        for field in postBodyParts:
                            fieldParts = field.split("=")
                            name = fieldParts[0]
                            value = fieldParts[1]
                            postDict[name] = value 

                # if request is invalid, send back 400 response
                if valid == 0:
                    print ("Returning 400: Bad Request")
                    s.sendall(str.encode("HTTP/1.0 400 Bad Request\r\n",'iso-8859-1'))
                else:
                    # if valid, try to retrieve the document
                    if reqType == 'POST':
                        reqFileName = reqURI[1:]
                    else:
                        reqFileName = 'static' + reqURI

                    try:
                        # open requested file 
                        reqFile = open(reqFileName, "r")

                        # read into a string
                        fileContents = reqFile.read() 

                        if reqType == 'POST':
                            for key, value in postDict.items():
                                searchKey = '{{' + key + '}}'
                                if fileContents.find(searchKey) != -1:
                                    fileContents = fileContents.replace(searchKey, value)
                                else:
                                    fileContents = fileContents.replace(searchKey, "??UN-KNOWN??")

                        #send to client
                        for o in outputready:
                            if o == s:
                                o.sendall(str.encode("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n",'iso-8859-1'))
                                o.sendall(str.encode(fileContents,'iso-8859-1'))

                        #close the file
                        reqFile.close()
                    except IOError:
                        # if not valid, send 404 back to client
                        print ("Returning 404: File Not Found")
                        s.sendall(str.encode("HTTP/1.0 404 Not Found\r\n",'iso-8859-1'))
            else:
                s.close() 
                inputreq.remove(s) 
                outputreq.remove(s)

# close socket              
sock.close()

