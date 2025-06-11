import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import base64
import json

class HttpServer:
    def __init__(self):
        self.sessions={}
        self.types={}
        self.types['.pdf']='application/pdf'
        self.types['.jpg']='image/jpeg'
        self.types['.txt']='text/plain'
        self.types['.html']='text/html'

    def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
        tanggal = datetime.now().strftime('%c')
        resp=[]
        resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
        resp.append("Date: {}\r\n" . format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n" . format(kk,headers[kk]))
        resp.append("\r\n")

        response_headers=''
        for i in resp:
            response_headers="{}{}" . format(response_headers,i)
        #menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
        #response harus berupa bytes
        #message body harus diubah dulu menjadi bytes
        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        #response adalah bytes
        return response

    def proses(self,data):
        requests = data.split("\r\n")
        #print(requests)

        baris = requests[0]
        #print(baris)

        all_headers = [n for n in requests[1:] if n!='']

        # Extract request body for POST requests
        request_body = ""
        if "\r\n\r\n" in data:
            request_body = data.split("\r\n\r\n", 1)[1]

        j = baris.split(" ")
        try:
            method=j[0].upper().strip()
            if (method=='GET'):
                object_address = j[1].strip()
                return self.http_get(object_address, all_headers)
            if (method=='POST'):
                object_address = j[1].strip()
                return self.http_post(object_address, all_headers, request_body)
            if (method=='DELETE'):
                object_address = j[1].strip()
                return self.http_delete(object_address, all_headers)
            else:
                return self.response(400,'Bad Request','',{})
        except IndexError:
            return self.response(400,'Bad Request','',{})

    def http_get(self,object_address,headers):
        files = glob('./*')
        #print(files)
        thedir='./'
        if (object_address == '/'):
            return self.response(200,'OK','Ini Adalah web Server percobaan',dict())
        if (object_address == '/video'):
            return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
        if (object_address == '/santai'):
            return self.response(200,'OK','santai saja',dict())
        if (object_address.startswith('/list/')):
            directory_name = object_address[6:]
            if directory_name == '':
                directory_name = '.'
            try:
                files_list = glob(f'{directory_name}/*')
                file_names = [os.path.basename(f) for f in files_list if os.path.isfile(f)]
                file_list_str = '\n'.join(file_names)
                return self.response(200,'OK',file_list_str,{'Content-type':'text/plain'})
            except:
                return self.response(404,'Directory Not Found','',{})

        object_address=object_address[1:]
        # print(object_address)
        if thedir+object_address not in files:
            return self.response(404,'Not Found','',{})
        fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
        #harus membaca dalam bentuk byte dan BINARY
        isi = fp.read()

        fext = os.path.splitext(thedir+object_address)[1]
        content_type = self.types.get(fext, 'application/octet-stream')

        headers={}
        headers['Content-type']=content_type

        return self.response(200,'OK',isi,headers)

    def http_post(self,object_address,headers, request_body):
        if object_address.startswith('/upload'):
            try:
                body_data = json.loads(request_body)
                filename = body_data.get('filename')
                file_content_b64 = body_data.get('content')

                if not filename or not file_content_b64:
                    return self.response(400,'Bad Request','Missing filename or content',{})

                file_content = base64.b64decode(file_content_b64)

                with open(filename, 'wb') as f:
                    f.write(file_content)

                return self.response(200,'OK',f'File {filename} uploaded successfully',{'Content-type':'text/plain'})
            except Exception as e:
                return self.response(500,'Internal Server Error',str(e),{})

        headers ={}
        isi = ""
        return self.response(404,'Not Found',isi,headers)

    def http_delete(self,object_address,headers):
        try:
            file_path = object_address[1:] if object_address.startswith('/') else object_address

            if os.path.exists(file_path):
                os.remove(file_path)
                return self.response(200,'OK',f'File {file_path} deleted successfully',{'Content-type':'text/plain'})
            else:
                return self.response(404,'Not Found','File not found',{})
        except Exception as e:
            return self.response(500,'Internal Server Error',str(e),{})
#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
    httpserver = HttpServer()
    # d = httpserver.proses('GET testing.txt HTTP/1.0')
    # print(d)
    # d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
    # print(d)
    # d = httpserver.proses('GET / HTTP/1.0')
    # print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)
