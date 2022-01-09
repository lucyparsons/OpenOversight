$(document).ready(function() {
    let overflow_length = 500;
    $(".incident-description").each(function () {
        let description = this;
        let incidentId = $( this ).data("incident");
        if (description.innerHTML.length < overflow_length) {
            $("#description-overflow-row_" + incidentId).hide();
        }
        if(description.innerHTML.length > overflow_length) {
            let originalDescription = description.innerHTML;
            description.innerHTML = description.innerHTML.substring(0, overflow_length) + "…";
            $(`#description-overflow-button_${incidentId}`).on('click', function(event) {
                event.stopImmediatePropagation();
                description.innerHTML = originalDescription;
                $("#description-overflow-row_" + incidentId).hide();
            })
        }
    })
});
