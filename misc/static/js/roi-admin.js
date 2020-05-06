function openSignin(key, id){
  var button = $('#btn-' + id);
  var span = $('#btn-text-' + id);
  button.addClass("progress-bar-striped progress-bar-animated");
  span.css({"padding-left": "6.5px"});
  $.ajax({
    url: "/api/v1/events/" + key + ":open",
    type: "POST",
    // dataType: "json",
    data: {"qwiklabs_token": 'abcd'}, //change token
    success: function(result){
      console.log(result);
      button.html('<span class="small" id="btn-text-' + id + '">End</span>');
      button.removeClass("progress-bar-striped progress-bar-animated btn-primary")
      button.addClass("btn-danger");
      button.attr('onclick', 'closeSignin("'+ key + '","' + id + '")');
      button.attr('id', 'btn-' + id);
    },
    error: function(xhr, status, errorThrown){
      console.log(errorThrown);
      console.log(status);
      console.log(xhr);
    }
  });
}

function closeSignin(key, id){
  var button = $('#btn-' + id);
  var span = $('#btn-text-' + id);
  button.addClass("progress-bar-striped progress-bar-animated");
  span.css({"padding-left": "10px"});
  $.ajax({
    url: "/api/v1/events/" + key + ":close",
    type: "POST",
    success: function(result){
      console.log(result);
      button.html('<span class="small" id="btn-text-' + id + '">Start</span>');
      button.removeClass("progress-bar-striped progress-bar-animated btn-danger");
      button.addClass("btn-primary");
      button.attr('onclick', 'openSignin("'+ key + '","' + id + '")');
      button.attr('id', 'btn-' + id);
    },
    error: function(xhr, status, errorThrown){
      console.log(errorThrown);
      console.log(status);
    }
  });
}

function signIn(id, key, email){
  $.ajax({
    url: "/api/v1/signins",
    data: {
      'user_email': email,
      'event_code': id,
      'url_safe_key': key
    },
    type: "POST",
    success: function(result){
      console.log(result);
    },
    error: function(xhr, status, errorThrown){
      console.log(errorThrown);
      console.log(status);
    }
  });
}

function openInNewTab(url){
  window.open(url, '_blank');
}
