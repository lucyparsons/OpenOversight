$(document).ready(function() {;
    const MODEL_URL = '/static/face_api_js_models'

    async function load_models(){
        await faceapi.loadFaceRecognitionModel(MODEL_URL)
        await faceapi.loadSsdMobilenetv1Model(MODEL_URL)
        await faceapi.loadFaceLandmarkModel(MODEL_URL)
    }

    load_models().then(result => result)

    async function get_faces(image){
        return await faceapi.detectAllFaces(image)
    }

    image = document.getElementById('image')
    $('#autodetector').click(function(e) {
        e.preventDefault();
        get_faces(image)
            .then((faces) => {
                faces.forEach(face => console.log(face))
            })
            .catch(error => console.log(error))
        });
});