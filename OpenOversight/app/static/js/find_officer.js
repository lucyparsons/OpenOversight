function buildSelect(name, data_url, dept_id) {
    return $.ajax({
        url: data_url,
        data: {department_id: dept_id}
    }).done(function(data) {
        $('input#' + name).replaceWith('<select class="form-control" id="' + name + '" name="' + name + '">');
        const dropdown = $('select#' + name);
        // Add the null case first
        dropdown.append(
            $('<option value="Not Sure">Not Sure</option>')
        );
        for (i = 0; i < data.length; i++) {
            dropdown.append(
                $('<option></option>').attr("value", data[i][1]).text(data[i][1])
            );
        }
    });
}

$(document).ready(function() {

    var navListItems = $('ul.setup-panel li a'),
        allWells = $('.setup-content');

    allWells.hide();

    navListItems.click(function(e)
    {
        e.preventDefault();
        var $target = $($(this).attr('href')),
            $item = $(this).closest('li');

        if (!$item.hasClass('disabled')) {
            navListItems.closest('li').removeClass('active');
            $item.addClass('active');
            allWells.hide();
            $target.show();
        }
    });

    let $deptSelectionId = $('#dept').val()

    $('ul.setup-panel li.active a').trigger('click');

    $('#dept').on('click', function(e) {
        e.preventDefault();
        $deptSelectionId = $('#dept').val();
    })

    $('#activate-step-2').on('click', function(e) {
        var dept_id = $('#dept').val();
        // fetch ranks for dept_id and modify #rank <select>
        var ranks_url = $(this).data('ranks-url');
        var units_url = $(this).data('units-url');
        buildSelect('rank', ranks_url, dept_id);
        buildSelect('unit', units_url, dept_id);

        $('ul.setup-panel li:eq(1)').removeClass('disabled');
        $('ul.setup-panel li a[href="#step-2"]').trigger('click');
        const depts_with_uii = $('#current-uii').data('departments');
        let targetDept = depts_with_uii.find(function(element) {
            return element.id == $deptSelectionId
        });
        let targetDeptUii = targetDept.unique_internal_identifier_label
        if (targetDeptUii) {
            $('#current-uii').text(targetDeptUii);
        } else {
            $('#uii-question').hide();
        }
        $(this).remove();
    })

    $('#activate-step-3').on('click', function(e) {
        $('ul.setup-panel li:eq(2)').removeClass('disabled');
        $('ul.setup-panel li a[href="#step-3"]').trigger('click');
        $(this).remove();
    })
    $('#activate-step-4').on('click', function(e) {
        $('ul.setup-panel li:eq(3)').removeClass('disabled');
        $('ul.setup-panel li a[href="#step-4"]').trigger('click');
        $(this).remove();
    })

    // Generate loading notification
    $("#user-notification").on("click", function(){
       $("#loader").show();
    });

    // Show/hide rank shoulder patches
    $("#show_img").on("click", function(){
       $("#hidden_img").show();
       $("#show_img_div").hide();
    });

    $("#hide_img").click(function(){
       $("#hidden_img").hide();
       $("#show_img_div").show();
    });
});
