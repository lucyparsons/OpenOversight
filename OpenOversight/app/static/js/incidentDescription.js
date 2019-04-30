$(document).ready(function() {
    

    $(".incident-description").each(function () {
        let description = this;
        let incidentId = $( this ).data("incident");
        if (description.innerText.length < 300) {
            $("#description-overflow-row_" + incidentId).hide();
        }
        if(description.innerText.length > 300) {
            description.innerText = description.innerText.substring(0, 300);
        }
    })
});