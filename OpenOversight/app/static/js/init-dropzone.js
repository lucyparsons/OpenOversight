/**
 * Initialize dropzone component
 * @param id element id
 * @param url url to upload to
 * @param csrf_token CSRF token
 * @return the Dropzone object
 */
function init_dropzone(id, url, csrf_token) {
    Dropzone.autoDiscover = false;

    let myDropzone = new Dropzone(id, {
      url: url,
      method: "POST",
      uploadMultiple: false,
      parallelUploads: 50,
      acceptedFiles: "image/png, image/jpeg, image/gif, image/jpg, image/webp",
      maxFiles: 50,
      headers: {
        'Accept': 'application/json',
        'X-CSRF-TOKEN': csrf_token
      },
      init: function() {
        this.on("error", function(file, response) {
          if (typeof(response) == "object") {
            response = response.error;
          }
          if (response.startsWith("<!DOCTYPE")) {
            // Catch any remaining HTML error pages
            response = "Upload failed.";
          }
          file.previewTemplate.appendChild(document.createTextNode(response));
        });
      }
    });
    return myDropzone;
}
