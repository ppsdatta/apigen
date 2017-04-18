(function (module) {
    
module.pnum = 1;

module.add_new = function (container_id) {
    var template = $('#param-template').html();
    var newelem = document.createElement('p');
    $(newelem).html(_.template(template)({num: module.pnum++}));
    $('#' + container_id).append(newelem);
    $('#numparams').val(module.pnum - 1);
};

module.show_hide = function(what) {
    var elem = $('#' + what);
    elem.toggle();
};

})(window);