'use strict'

$(document).ready(function () {
    $('.js-add-another-button').click(function (event) {
        event.preventDefault()
        console.log($(event.target.previousElementSibling))
        cloneField($(event.target.previousElementSibling));
    });
    $('.js-remove-button').click(removeField)
    $('button').removeAttr('disabled')
});

/*
    This function clones the element matching the given selector
    It looks for numbers in the element's id and increments them by 1
    It attaches the new element to the DOM directly after the cloned element
*/
function cloneField(selector) {
    var new_element = $(selector).clone(true);
    var elem_id = new_element.nodeName === 'INPUT'? new_element.id : new_element.find(':input')[0].id;
    var elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-?.*/m, '$1')) + 1;
    var matchRegex = new RegExp('-' + (elem_num - 1) + '(-?)')
    var replaceString = '-' + elem_num + '$1'
    new_element.find(':input').each(function() {
        if($(this).attr('id')){
            var id = $(this).attr('id').replace(matchRegex, replaceString);
            $(this).attr({'name': id, 'id': id})
            // don't delete the value of the csrf token
            if($(this).attr('name').indexOf('csrf') == -1){
                $(this).val('').removeAttr('checked');
            }
        }
    });

    new_element.find('button').click(removeField)
    $(selector).after(new_element);
    new_element.find('div').show()
}


/* This function checks if it is the last fieldset element in its parent. If it is, it removes all field values before hiding the element, and sets a new click handler and text on the add button. If it has other fieldset siblings, it simply deletes itself. */

function removeField(event) {
    event.preventDefault();
    var $lastElement = $(event.target).closest('div')
    // Remove any filled in values (but not the csrf token)
    $lastElement.find(':input[type=text]:not(:hidden)').each(function(child) {
        $(this).val('')
    });
    $lastElement.hide()
}
