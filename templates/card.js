
           function sendRequest{{ uuid }}(fd, loc) {
                var xhr = new XMLHttpRequest();
                xhr.onload = function(e) {
                    if (this.readyState === 4) {
                        console.log("Server returned: ", e.target.responseText);
                        if (e.target.responseText != "Error") {
                            meetingId = e.target.responseText
                            $( "#span{{ uuid }}" ).html("<button type=\"button\" class=\"btn btn-outline-info\" onclick=\"window.open('https://zoom.us/j/" + meetingId + "');\">Join Zoom Meeting (id: " + meetingId + ")</button>");
                        } 
                    }
                };
                xhr.timeout = 5000;
                xhr.open("POST", loc, true);
                xhr.send(fd);
                console.log(fd);
                for (var value of fd.values()) {
                   console.log("{{ uuid }}", value);
                }
                for (var value of fd.keys()) {
                   console.log("{{ uuid }}", value);
                }
            }

            function submit{{ uuid }}() {
                var fd = new FormData();
                fd.append("meeting_id", document.getElementsByClassName("meeting_id{{ uuid }}")[0].value);
                fd.append("course", "{{ course }}");
                fd.append("section", "{{ sec }}");
                sendRequest{{ uuid }}(fd, "update");
            }

            $(window).on('load', function() {
                $( "#meeting_id{{ uuid }}" ).keyup(function() {
                  submit{{ uuid }}();
                  console.log( "Handler for {{ uuid }} called." );
                });
            });
