function buildSelect(name, data_url, dept_id) {
    return $.get({
        url: data_url,
        data: {department_id: dept_id}
    }).done(function(data) {
        const dropdown = $(
            '<select class="form-select" id="' + name + '" name="' + name + '">'
        );
        // Add the null case first
        dropdown.append($('<option value="Not Sure">Not Sure</option>'));
        for (const item of data) {
            dropdown.append(
                $('<option></option>').attr('value', item[1]).text(item[1])
            );
        }
        $('#' + name).replaceWith(dropdown);
    });
}

$(document).ready(function() {
    // Load the department's units and ranks when a new dept is selected
    $('#dept').on('change', e => {
        const deptId = $('#dept').val();
        const ranksUrl = $('#step-1').data('ranks-url');
        const unitsUrl = $('#step-1').data('units-url');
        buildSelect('rank', ranksUrl, deptId);
        buildSelect('unit', unitsUrl, deptId);

        const deptsWithUii = $('#current-uii').data('departments');
        const targetDept = deptsWithUii.find((element) => element.id == deptId);

        const deptUiidLabel = targetDept.unique_internal_identifier_label;
        if (deptUiidLabel) {
            $('#current-uii').text(deptUiidLabel);
            $('#uii-question').show();
        } else {
            $('#uii-question').hide();
        }
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
    $('#dept').trigger('change');
});
