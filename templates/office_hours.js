
           function sendRequest{{ uuid }}(fd, loc) {
                var xhr = new XMLHttpRequest();
                xhr.onload = function(e) {
                    if (this.readyState === 4) {
                        console.log("Server returned: ", e.target.responseText);
                        if (e.target.responseText != "Error") {
                            meetingId = e.target.responseText
                            $( "#span{{ uuid }}" ).html("<button style=\"background-color: rgb(0,147,213); font-family: Montserrat; margin: 5px;\" type=\"button\" class=\"btn waves-effect waves-light\" onclick=\"window.open('https://zoom.us/j/" + meetingId + "');\">Join Class<span id=\"full-text\"> (id: " + meetingId + ")</span></button>");
                            M.toast({html: 'Meeting ID successfully changed to ' + e.target.responseText + "."})
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

            function sendDescRequest{{ uuid }}(fd, loc) {
                var xhr = new XMLHttpRequest();
                xhr.onload = function(e) {
                    if (this.readyState === 4) {
                        console.log("Server returned: ", e.target.responseText);
                        if (e.target.responseText !== "Error") {
                            M.toast({html: 'Description Successfully Saved'})
                        } else {
                            M.toast({html: 'Description Failed To Save'})
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
                fd.append("course", "Office Hours");
                fd.append("section", "ID");
                sendRequest{{ uuid }}(fd, "update");
            }

            function submit_desc{{ uuid }}() {
                var fd = new FormData();
                fd.append("meeting_id", document.getElementById("office_desc{{ uuid }}").value);
                fd.append("course", "Office Hours");
                fd.append("section", "DESC");
                sendDescRequest{{ uuid }}(fd, "update");
            }

            $(window).on('load', function() {
                $("#office_desc{{ uuid }}").val("{{ office_desc }}");

                $( "#meeting_id{{ uuid }}" ).keyup(function() {
                  submit{{ uuid }}();
                  console.log( "Handler for {{ uuid }} called." );
                });
            });
