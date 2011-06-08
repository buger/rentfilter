function filterAds(){                
    if (!$('.filter').is(':visible'))
        return

    var filter_type = $('.filter a.active').data('filter');

    $('.estate_links li > a').each(function(){                
        if (this.parentNode.className == 'load_more')
            return;

        var hide = false;

        var ban_words = /(сниму|снимем|помогу|снимет)/;
        var hourly_words = /(посуточно|посуточная|сутки)/;
        
        if (filter_type == 'hourly') {
            if (!this.innerHTML.match(hourly_words)) {
                hide = true
            }
        } else {
            if (this.innerHTML.match(hourly_words)) {
                hide = true
            }
        }

        if (!hide && this.innerHTML.match(ban_words)) {
            hide = true;
        }

        if (hide) {
            this.parentNode.style.display = 'none';
        } else {
            this.parentNode.style.display = 'block';
        }
    });
}

$(function(){
    filterAds();
});

$('.filter a').click(function(){
    $(this).parent().find('.active').removeClass("active");

    $(this).addClass('active');
    
    filterAds();
});

$('.load_more a').bind('click', function(){
    var self = this;
    this.innerHTML = 'Загрузка...'
    var cursor = $(this).data('cursor');
    var start_from = $(this).data('start-from');

    $.getJSON('/', {cursor: cursor, start_from: start_from }, 
        function(data){
            if (data.html.length <= 1) {
                return $(self.parentNode).hide();
            }

            $(self).data('cursor', data.cursor);
            $(self).data('start_from', data.start_from);
            
            var latest_time = $(self.parentNode).prevAll('li.time').find('span')[0].innerHTML;
            
            var temp = $("<div/>").append(data.html);
            var first_time = temp.find('li.time:first');
            if (first_time.find('span')[0].innerHTML == latest_time) {
                first_time.prev().remove();
                first_time.remove();
            }

            console.log(temp);

            $(self.parentNode).before(temp[0].innerHTML);

            self.innerHTML = 'Загрузить еще';

            filterAds();
        }                    
    );
});

$('.about_link').bind('click', function(){
    window.scrollTo(0, document.body.scrollHeight);
});

$('.move_up').bind('click', function(){
    window.scrollTo(0, 0);
});

$('.estate_links li').tooltip({ delay: 500 });

$('.select_town').live('click', function(){
    $(this).find('.towns').toggle();
    $(this).toggleClass('opened');
});

function renderSVG(context, name, options) {
    if (!options)
        options = {};

    var set = context.set();
    for (var i=0; i<images[name].length; i++) {
        try {
            set.push(context.path(images[name][i]));
        } catch (e) {}
    }

    set.attr({fill: "#403B33", stroke: "none"}).attr(options);
    
    return set;
}

$('#about .images').show();

var animations = [['head', -70], ['phone', -20], ['arrive', -110], ['donate', -20]];
var container = $('#about .images div')[0];
var main = new ScaleRaphael(container, 500, 500);
main.scaleAll(3.8);

function animate(frame) {
    if (frame >= animations.length) {
        frame = 0;
    }

    $(container).parent().css({right: animations[frame][1]});
    $(container).fadeIn('slow');

    main.clear();
    renderSVG(main, animations[frame][0]);                
    
    $(container).delay(2000).fadeOut('slow', function(){                    
        animate(frame+1);
    });                
}

animate(0);

var shower = new ScaleRaphael($('.shower div')[0], 400, 400);                         
shower.scaleAll(3);
var set = renderSVG(shower, 'shower', {fill:"white"});            

var animate_shower = true;
set[0].node.onclick = function(){
    if (animate_shower) {
        animate_shower = false;
        set.show();
    } else {
        animate_shower = true;
    }
}

var lines = [[8,7,6,5,4,3], [14,13,12,11,10,9], [20,19,18,17,16,15], [21,22,23,24,25,26]];

for (var j=0; j<lines.length; j++) {
    (function(items){
        var active_index = 0;
        function animateShower(indexes){
            if (animate_shower) {
                if (active_index > indexes.length) {
                    active_index = 0;
                }

                for(var i=0; i<indexes.length; i++) {
                    set[indexes[i]].show();

                    if (active_index == i) {
                        set[indexes[i]].hide();
                    }
                }
                
                active_index += 1;

            }
            
            setTimeout(function(){
                animateShower(indexes);
            }, 50);
        }
        
        setTimeout(function(){
            animateShower(items);
        }, Math.floor(Math.random()*1000));
    }(lines[j]));
}

$(document).ready(function($) {
    $('a[rel*=facebox]').facebox() 
});

$('#facebox .send_donation').live('click', function(){
    var url = "https://sites.fastspring.com/chromusapp/instant/rentfilterru?tags=price=";

    console.log('asd');

    document.location = url + parseInt($('#facebox .donation').val());
});

$('#other_towns').bind('click', function(){
    $.facebox({div: "#other_towns_popup"});
});

