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

module.update_endpoint = function () {
    var endpoint = 'https://api.projectplace.com/api/v';
    var version = $('#apiVersion').val();
    var category = $('#apiCategory').val();
    endpoint += version + '/' + category + '/';
    $('#endpoint-hint').html(endpoint);
};

$(document).ready(function () {
    module.update_endpoint();
});

})(window);