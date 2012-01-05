(function(window, undefined){
    window._rfq = window._rfq || [];

    // Function.prototype.bind polyfill
    if ( !Function.prototype.bind ) {

      Function.prototype.bind = function( obj ) {
        if(typeof this !== 'function') // closest thing possible to the ECMAScript 5 internal IsCallable function
          throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');

        var slice = [].slice,
            args = slice.call(arguments, 1), 
            self = this, 
            nop = function () {}, 
            bound = function () {
              return self.apply( this instanceof nop ? this : ( obj || {} ), 
                                  args.concat( slice.call(arguments) ) );    
            };

        bound.prototype = this.prototype;

        return bound;
      };
    }

    function hashToQueryString(hash) {
        var params = [];

        for (key in hash) {
            if (hash.hasOwnProperty(key)) {
                params.push(key + "=" + hash[key]);
            }
        }

        return params.join('&');
    }
    
    var JSONP = function(url, callback) {        
        var script = document.createElement('script');

        script.setAttribute('src', url + '&callback=' + callback);

        document.getElementsByTagName('head')[0].appendChild(script);
    };

    var RentFilterAPI = function(){
        this.host = "http://russiaflatrent.appspot.com";
    };

    RentFilterAPI.prototype.check_urls = function(urls, callback){        
        if (!callback) callback = function(){}

        var callback_name = "rf_cb_" + (+new Date());

        window[callback_name] = function(items) {
            callback(items);

            delete window[callback_name];
        }

        var host = urls[0].match(/:\/\/(.[^/]+)/)[1];        

        var params = [];

        for (var i=0; i < urls.length; i++) {
            // Trying to minimize query string becouse of limitations of JSONP (HTTP GET 2048 url length limit)
            params.push("u[]=" + urls[i].replace(/http:\/\//,'').replace(host, '').replace(/\?.*/,'')); 
        }

        params.push("host=" + host); 

        if (this.api_key) params.push("api_key=" + this.api_key);

        JSONP(this.host+'/api/check_urls?'+params.join('&'), callback_name);
    }

    RentFilterAPI.prototype.check_phones = function(phones, callback){
        if (!callback) callback = function(){}

        var callback_name = "rf_cb_" + (+new Date());

        window[callback_name] = function(items) {
            callback(items);

            delete window[callback_name];
        }

        var params = [];

        for (var i=0; i < urls.length; i++) {
            // Trying to minimize query string because of JSONP limitations (HTTP GET 2048 url length limit)
            params.push("p[]=" + urls[i].replace(/\D/,'')); 
        }
        
        if (this.api_key) params.push("api_key=" + this.api_key);

        JSONP(this.host+'/api/check_phones?'+params.join('&'), callback_name);
    }   

    window.rf_api = new RentFilterAPI();
}(window))


/*
<script src="http://russiaflatrent.appspot.com/js/api.js"></script>
<script>
rf_api.api_key = 'key';

rf_api.check_urls(['http://ad_url3', 'http://ad_url4'], function(items){
    for (var i=0; i<items.length; i++) {
        if (items[i].agent)
            $('a[href="'+items[i].url+'"]).parent().addClass('agent');
    }
});

</script>
*/
