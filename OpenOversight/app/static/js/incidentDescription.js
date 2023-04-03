$(document).ready(function() {
    const overflow_length = 700;
    $(".incident-description").each(function () {
        let description = this;
        let incidentId = $( this ).data("incident");
        if (description.innerHTML.length <= overflow_length) {
            $("#description-overflow-row_" + incidentId).hide();
        } else {
            let originalDescription = description.innerHTML;
            // Convert the innerHTML into a string, and truncate it to overflow length
            const sub = description.innerHTML.substring(0, overflow_length);
            // In order to make the cutoff clean, we will want to truncate *after*
            // the end of the last HTML tag. So first we need to find the last tag.
            const cutoff = sub.lastIndexOf("</");
            // Tags could be variable length, so next find the index of the first
            // ">" after the start of the closing bracket.
            const lastTag = sub.substring(cutoff).indexOf(">");
            // Lastly, trim the HTML to the end of the closing tag, if a tag was found
            if (cutoff == -1 || lastTag == -1) {
                description.innerHTML = sub;
            } else {
                description.innerHTML = sub.substring(0, cutoff + lastTag + 1);
            }
            description.innerHTML += "…";

            $(`#description-overflow-button_${incidentId}`).on('click', function(event) {
                event.stopImmediatePropagation();
                description.innerHTML = originalDescription;
                $("#description-overflow-row_" + incidentId).hide();
            })
        }
    })
});
