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
        const canvas = faceapi.createCanvasFromMedia(image)
        document.body.append(canvas)
        const displaySize = { width: image.width, height: image.height }
        console.log('displaySize', displaySize)
        get_faces(image)
            .then((face_detections) => {
                face_detections.forEach(face_detection => console.log(face_detection))
                console.log('face_detections', face_detections)
                const resizedDetections = faceapi.resizeResults(face_detections, displaySize)
                faceapi.draw.drawDetections(canvas, resizedDetections)
            })
            .catch(error => console.log(error))
        });
});