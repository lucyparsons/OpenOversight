'use strict'

$(document).ready(function () {
    console.log('Ready')
    $('button').removeAttr('disabled')
    $('.js-add-another-button').click(function (event) {
        console.log('click!')
        event.preventDefault()
        clone_field_list($(event.target.previousElementSibling));
    });
    $('.js-remove-button').click(removeParent)
});

function clone_field_list(selector) {
    var new_element = $(selector).clone(true);
    var elem_id = new_element.find(':input')[0].id;
    var elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
    var matchRegex = new RegExp('-' + (elem_num - 1) + '(-?)')
    var replaceString = '-' + elem_num + '$1'
    new_element.find(':input').each(function() {
        if($(this).attr('id')){
            var id = $(this).attr('id').replace(matchRegex, replaceString);
            $(this).attr({'name': id, 'id': id})
            // don't delete the value of the csrf token
            if($(this).attr('name').indexOf('csrf') == -1){
                $(this).attr({'name': id, 'id': id}).val('').removeAttr('checked');
            }
        }
    });

    new_element.find('label').each(function() {
        var new_for = $(this).attr('for').replace(matchRegex, replaceString);
        $(this).attr('for', new_for);
    });
    new_element.find('button').click(removeParent)
    $(selector).after(new_element);
}

function removeParent(event) {
    event.preventDefault()
    event.target.parentElement.remove()
}
