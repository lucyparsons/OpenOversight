$(document).ready(function () {
    const img = $("#face-img")
    const frame = $("#face-tag-frame")

    // To prevent hi-res images from taking over the entire page, the image is being shown
    // in a responsive element. This means we need to compute the tag frame dimensions using
    // percentages so it will scale if the page size changes.

    // To do this, we're dividing the tag dimensions by the image's actual width/height and
    // multiplying by 100.
    const tagWidth = parseInt(img.data("width")) / img[0].naturalWidth * 100
    const tagHeight = parseInt(img.data("height")) / img[0].naturalHeight * 100
    const tagLeft = parseInt(img.data("left")) / img[0].naturalWidth * 100
    const tagTop = parseInt(img.data("top")) / img[0].naturalHeight * 100

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
