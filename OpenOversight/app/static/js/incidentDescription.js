$(document).ready(function() {
    $(".incident-description").each(function () {
        let description = this;
        let incidentId = $( this ).data("incident");
        if (description.innerText.length < 300) {
            $("#description-overflow-row_" + incidentId).hide();
        }
        if(description.innerText.length > 300) {
            let originalDescription = description.innerText;
            description.innerText = description.innerText.substring(0, 300);
            $(`#description-overflow-button_${incidentId}`).on('click', function(event) {
                description.innerText = originalDescription;
                $("#description-overflow-row_" + incidentId).hide();
            })
        }
    })
});
