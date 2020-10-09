'use strict'

$(document).ready(function () {
    $('.js-add-another-button').click(function (event) {
        event.preventDefault()
        cloneFieldList($(event.target.previousElementSibling));
    });
    $('.js-remove-button').click(removeParent)
    $('button').removeAttr('disabled')
});

/*
    This function clones the element matching the given selector
    It looks for numbers in the element's id and increments them by 1
    It attaches the new element to the DOM directly after the cloned element
*/
function cloneFieldList(selector) {
    if ($(selector).is(':hidden')) {
        $(selector).show();
    } else {
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

        new_element.find('label').each(function() {
            var old_for = $(this).attr('for')
            if (old_for) {
                var new_for = old_for.replace(matchRegex, replaceString);
                $(this).attr('for', new_for);
            }
        });
        new_element.find('button').click(removeParent)
        $(selector).after(new_element);
    }
}


/* This function checks if it is the last fieldset element in its parent. If it is, it removes all field values before hiding the element. If it has other fieldset siblings, it simply deletes itself. */

function removeParent(event) {
    event.preventDefault()
    if ($(event.target.parentElement.parentElement).find('fieldset').length > 1) {
        event.target.parentElement.remove();
    } else {
        // Remove any filled in values (but not the csrf token)
        $(event.target.parentElement).find(':input:not(:hidden)').each(
            function(child) {
                $(this).val('')
            }
        )
        $(event.target.parentElement).hide();
    }
}
