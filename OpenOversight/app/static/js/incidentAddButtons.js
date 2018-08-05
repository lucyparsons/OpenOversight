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
        var new_for = $(this).attr('for').replace(matchRegex, replaceString);
        $(this).attr('for', new_for);
    });
    new_element.find('button').click(removeParent)
    $(selector).after(new_element);
}


/* This function checks if it is the last fieldset element in its parent. If it is, it removes all field values before hiding the element, and sets a new click handler and text on the add button. If it has other fieldset siblings, it simply deletes itself. */

function removeParent(event) {
    event.preventDefault()
    var things_to_add;
    things_to_add = {"Plate Number" : "license plate", "Link" : "link", "OO Officer ID" : "officer"};
    var previousElement = event.target.parentElement.previousElementSibling
    var nextElement = event.target.parentElement.nextElementSibling

    if(previousElement && nextElement){
        var $lastElement = $(event.target.parentElement)
        // Remove any filled in values (but not the csrf token)
        $lastElement.find(':input:not(:hidden)').each(function(child) {
            $(this).val('')
        });
        $lastElement.hide()
        var add_button = $(nextElement)
        var fieldsetName = $(previousElement).text().slice(0, -1)
        for (var key in things_to_add) {
             if(fieldsetName.search(key) != -1) {
                fieldsetName = things_to_add[key]
                break;
             }
        }

        // nextElement's textContent is short, like
        // "Add another link" when we're removing the last element added
        // When we are removing something that is not the
        // last element added, it is huge (the whole input form)
        // with lots of whitespace.
        // If we're not removing the last element added,
        // we already have a valid Add button so we don't
        // want to create another
        if (nextElement.textContent.length <= 40) {
             // Remove previous click handler
             add_button.off('click')
             add_button.text('Add another ' + fieldsetName)
             add_button.on('click', function(event) {
                  event.preventDefault()
                  $lastElement.show()
                  // remove this click handler
                  add_button.off('click')
                  add_button.text('Add another ' + fieldsetName)
                  // restore the previous add function
                  add_button.click(function (event) {
                      event.preventDefault()
                      cloneFieldList($(event.target.previousElementSibling));
                 });
             })
        }
   }
}
