

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};



$(function() {
  var conn = null;
  var old_title = document.title
  var flag=false;
  
  function log(msg) {
    var control = $('#log');
    control.html(control.html() + msg + '<br/>');
    control.scrollTop(control.scrollTop() + 1000);
  }
  
  function newMsgCount(){
      if(flag){
        flag=false;
        document.title='【新消息】';
      }else{
        flag=true;
        document.title='【　　　】';
      }

  }
  
  function connect() {
    disconnect();
    var transports = ["websocket","xhr-streaming","iframe-eventsource","iframe-htmlfile","xhr-polling","iframe-xhr-polling"];
    conn = new SockJS('http://' + window.location.host + '/chat', transports);
    log('Connecting...');
    conn.onopen = function() {
        log('Connected.');
        update_ui();
    };
    conn.onmessage = function(e) {
        log(e.data);
        var hidden = true;
        if(document.hidden!=undefined){
            hidden = document.hidden
        }
        if(document.title==old_title && hidden){
            newMsgCount();
            var interval = window.setInterval('newMsgCount()',380);
            window.onmouseover = function (e) {
                document.title = old_title;
                window.clearInterval(interval);
            }
        }
        
    };
    conn.onclose = function() {
        log('Disconnected.');
        conn = null;
        update_ui();
    };
  }
  
  
  function disconnect() {
    if (conn != null) {
        log('Disconnecting...');
        conn.close();
        conn = null;
        update_ui();
    }
  }
  
  //when conn have message or status change, update
  function update_ui() {
    var msg = '';
    if (conn == null || conn.readyState != SockJS.OPEN) {
        $('#status').text('disconnected');
        $('#connect').text('Connect');
    } else {
        $('#status').text('connected (' + conn.protocol + ')');
        $('#connect').text('Disconnect');
    }
  }
  
  //connect or disconnect
  $('#connect').click(function() {
    if (conn == null) {
        connect();
    } else {
        disconnect();
    }
    update_ui();
    return false;
  });
  
  // submit
  $('form').submit(function() {
    var message = $('#chatform').formToDict();
    //log('Sending: ' + text);
    conn.send(JSON.stringify(message));
    $('#text').val('').focus();
    return false;
  });
});
