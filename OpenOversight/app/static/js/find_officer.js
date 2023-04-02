function buildSelect(name, data_url, dept_id) {
    return $.get({
        url: data_url,
        data: {department_id: dept_id}
    }).done(function(data) {
        const dropdown = $(
            '<select class="form-control" id="' + name + '" name="' + name + '">'
        );
        // Add the null case first
        dropdown.append($('<option value="Not Sure">Not Sure</option>'));
        for (let i = 0; i < data.length; i++) {
            dropdown.append(
                $('<option></option>').attr('value', data[i][1]).text(data[i][1])
            );
        }
        $('#' + name).replaceWith(dropdown);
    });
}

$(document).ready(function() {
    const navListItems = $('ul.setup-panel li a');
    const navButtons = $('.setup-content a');
    const allWells = $('.setup-content');

    // If a navigation bar item is clicked and is not disabled, activate the selected panel
    navListItems.click(function(e) {
        const $target = $($(this).attr('href'));
        const $item = $(this).parent();

        if (!$item.hasClass('disabled')) {
            navListItems.parent().removeClass('active');
            $item.addClass('active');
            allWells.addClass("hidden");
            $target.removeClass("hidden");
        }

        return false;
    });

    // When next or previous button is clicked, simulate clicking on navigation bar item
    navButtons.click(function(e) {
        const stepId = $(this).attr('href');
        // Locate the nav bar item for this step
        const $navItem = $('ul.setup-panel li a[href="' + stepId + '"]');

        $navItem.parent().removeClass('disabled');
        $navItem.trigger('click');

        return false;
    })

    // Load the department's units and ranks when a new dept is selected
    $('#dept').on('change', function(e) {
        const deptId = $('#dept').val();
        const ranksUrl = $('#step-1').data('ranks-url');
        const unitsUrl = $('#step-1').data('units-url');
        buildSelect('rank', ranksUrl, deptId);
        buildSelect('unit', unitsUrl, deptId);

        const deptsWithUii = $('#current-uii').data('departments');
        const targetDept = deptsWithUii.find(function(element) {
            return element.id == deptId
        });

        const deptUiidLabel = targetDept.unique_internal_identifier_label
        if (deptUiidLabel) {
            $('#current-uii').text(deptUiidLabel);
        } else {
            $('#uii-question').hide();
        }

        // Disable later steps if dept changed in case ranks/units have changed
        $('ul.setup-panel li:not(.active)').addClass('disabled');
    });

    // Generate loading notification
    $('#user-notification').on('click', function(){
       $('#loader').show();
    });

    // Show/hide rank shoulder patches
    $('#show-img').on('click', function(){
       $('#hidden-img').show();
       $('#show-img-div').hide();
    });

    $('#hide-img').click(function(){
       $('#hidden-img').hide();
       $('#show-img-div').show();
    });

    // Advance to the next screen on "Enter" keypress. Implementing this
    // manually because the default Enter behavior varies across browsers
    // https://stackoverflow.com/a/925387
    $("form input").on("keypress", function (e) {
        if (e.keyCode == 13) {
            $(".setup-content:not(.hidden) .next").trigger("click");
            return false;
        }
    });

    // Initialize controls
    allWells.addClass("hidden");
    $('#dept').trigger('change');
    $('ul.setup-panel li.active a').trigger('click');
});
