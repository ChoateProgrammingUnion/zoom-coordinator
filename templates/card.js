            function submit{{ uuid }}() {
                var fd = new FormData();
                fd.append("meeting-id", document.getElementsByClassName("meeting_id{{ uuid }}")[0].value);
                fd.append("course", "{{ course }}");
                fd.append("section", "{{ sec }}");
                sendRequest(fd, "update");
            }
            $( ".meeting_id{{ uuid }}" ).keypress(function() {
              submit{{ uuid }};
              console.log( "Handler for {{ uuid }} called." );
            });


