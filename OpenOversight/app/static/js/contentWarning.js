function createOverlay(container) {
    const warningText = $(
        "<span><h3>Content Warning</h3><p>This video may be disturbing for some viewers</p></span>"
    )
    const hide = $('<button type="button" class="btn btn-lg btn-light">Show video</button>')
    hide.click(() => overlay.css("display", "none"))

    const wrapper = $("<div>")
    wrapper.append(warningText)
    wrapper.append(hide)

    const overlay = $('<div class="overlay">')
    overlay.append(wrapper)
    container.append(overlay)
}

$(document).ready(() => {
    $(".video-container").each((index, element) => {
        const container = $(element)
        if (container.data("has-content-warning")) {
            createOverlay(container)
        }
    })
})
