function isNumeric(value) {
    return /^\d+$/.test(value)
}

$(document).ready(function () {
    const img = $("#face-img")
    const frame = $("#face-tag-frame")

    const frameWidth = img.data("width")
    const frameHeight = img.data("height")
    const frameLeft = img.data("left")
    const frameTop = img.data("top")

    if ([frameWidth, frameHeight, frameLeft, frameTop].every(isNumeric)) {
        img.one("imageLoaded", function () {
            // To prevent hi-res images from taking over the entire page, the image is being shown
            // in a responsive element. This means we need to compute the tag frame dimensions
            // using percentages so it will scale if the page size changes.

            // To do this, we're dividing the tag dimensions by the image's actual width/height and
            // multiplying by 100.
            const tagWidth = parseInt(frameWidth) / img[0].naturalWidth * 100
            const tagHeight = parseInt(frameHeight) / img[0].naturalHeight * 100
            const tagLeft = parseInt(frameLeft) / img[0].naturalWidth * 100
            const tagTop = parseInt(frameTop) / img[0].naturalHeight * 100

            frame.css({
                height: tagHeight + "%",
                width: tagWidth + "%",
                left: tagLeft + "%",
                top: tagTop + "%",
                visibility: "visible",
            })

            // Make sure wrapper does not expand larger than image
            $(".face-wrap").css("maxWidth", img[0].naturalWidth + "px")
        });

        img.on("load", function () {
            img.trigger("imageLoaded")
        })

        // Handle case where image was cached and is loaded before handler is registered
        if (img[0].complete) {
            img.trigger("imageLoaded")
        }
    }
});
