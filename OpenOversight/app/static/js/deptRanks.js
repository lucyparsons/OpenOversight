'use strict'

$(document).ready(function () {
    $('.js-add-another-button').click(function (event) {
        event.preventDefault();
        cloneField($(event.target.previousElementSibling));
    });
    $('.js-remove-button').click(removeField);
    $('button').removeAttr('disabled');
    $( ".sortable" ).sortable({
      items: "> fieldset",
      cursor: "move",
      update: renumberFields
    });
    renumberFields();
});

/*
    This function clones the element matching the given selector
    It looks for numbers in the element's id and increments them by 1
    It attaches the new element to the DOM directly after the cloned element
*/
function cloneField(selector) {
  if ($(selector).is(':hidden')) {
    $(selector).show();
  } else {
    var new_element = $(selector).clone(true);
    new_element.find('input[type=text]').each(function() {
      $(this).val('').removeAttr('checked');
    });
    new_element.find('button').click(removeField);
    $(selector).after(new_element);
    new_element.find('div').show();
    renumberFields();
  }
}

function renumberFields(event, ui) {
  var i = 0;
  $('.sortable-fields').find('fieldset input:not(:hidden)[type="text"]').each(function() {
    $(this).attr({'name': 'jobs-' + i, 'id': 'jobs-' + i})
    i++;
  });
}

/* This function checks if it is the last fieldset element in its parent. If it is, it removes all field values before hiding the element. If it has other fieldset siblings, it simply deletes itself. */
function removeField(event) {
    event.preventDefault();
    if ($(event.target).closest('div.sortable-fields').find('fieldset').length > 1) {
      $(event.target).closest('fieldset').remove();
    } else {
      var $lastElement = $(event.target).closest('fieldset');
      // Remove any filled in values (but not the csrf token)
      $lastElement.find(':input[type=text]').each(function(child) {
          $(this).val('');
      });
      $lastElement.hide();
    }
}
