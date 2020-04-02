# Postmortem for Reliability Issues on Tuesday, March 31st
By: Max Fan

Tuesday was a tough day for the backend part of the team (me and Ethan). We did not know that our system was going to be massively tested by the entire faculty until feedback and errors flooded into our emails and logs (very helpful!). At this time our logs were quite minimal and just kept track of any errors thrown by the code.

The first thing we did was implement better logging. We could not determine who or what was causing our errors and had now way of determining what happened on the server.

After some checking, we realized that we were validating people's accounts by checking against the first name and last name that Google's OAuth API was giving to us. This was problematic for a variety of reasons, mainly because we found out through our error logs that people were allowed to change their first name and last name on their Google account. This means that teachers could, in theory, impersonate other teachers and our servers would have not objected such malicious activity.

Additionally, account names like "The Rev. . ." introduced other problems since we did not expect non-alphabetical characters to show up in the first name or last name. As a result of this discovery, we decided to ask for email accounts to be given to us along with each teacher's name. At this point, we were already down for two critical hours and were getting numerous complaints and feedback from our teachers.

In the meantime, we worked on fixing other issues discovered in the logs. One bug we were able to discover, as a result of aggressive testing searching for different bugs, was a subtle [race condition](https://en.wikipedia.org/wiki/Race_condition) in either [Sqlite](https://www.sqlite.org/index.html) or [Dataset](https://dataset.readthedocs.io/en/latest/), the database libraries we were using. When multiple users were reading/writing to the same database at the same time, there were some strange unexplainable errors that were fixed by implementing a file locking solution that allowed only one write at a time.

At this time, we attempted to manually fix broken logins because we felt that we couldn't wait and let down faculty who were expecting a high-performance, well-written, and reliable website. The problem with this was – how do we change the database live in production? Since only roughly a quarter of faculty were able to use the website at this time, we decided to take the site offline for half an hour and update the database manually.

The final issue was: 
```
ERROR:app:Exception on /update [POST]
Traceback (most recent call last):
  File "/usr/local/lib/python3.8/urllib/request.py", line 1319, in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
  File "/usr/local/lib/python3.8/http/client.py", line 1230, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/local/lib/python3.8/http/client.py", line 1276, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/local/lib/python3.8/http/client.py", line 1225, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/local/lib/python3.8/http/client.py", line 1004, in _send_output
    self.send(msg)
  File "/usr/local/lib/python3.8/http/client.py", line 944, in send
    self.connect()
  File "/usr/local/lib/python3.8/http/client.py", line 1399, in connect
    self.sock = self._context.wrap_socket(self.sock,
  File "/usr/local/lib/python3.8/ssl.py", line 500, in wrap_socket
    return self.sslsocket_class._create(
  File "/usr/local/lib/python3.8/ssl.py", line 1040, in _create
    self.do_handshake()
  File "/usr/local/lib/python3.8/ssl.py", line 1309, in do_handshake
    self._sslobj.do_handshake()
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1108)
```
Zoom was down. At this point we decided to remove our Zoom-checking function and rely on our internal validation of Zoom links.


## Takeaways and Lessons Learned
- Verbose logs are always better
- Always aggressively test
- Vet the quality of the data you're getting
- Establish clear communication about when a project is ready for production
- Avoid updating your DB in production
