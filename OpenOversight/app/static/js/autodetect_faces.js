$(document).ready(function() {;
    const MODEL_URL = '/static/face_api_js_models'

    async function loadModels(){
        await faceapi.loadFaceRecognitionModel(MODEL_URL)
        await faceapi.loadSsdMobilenetv1Model(MODEL_URL)
        await faceapi.loadFaceLandmarkModel(MODEL_URL)
    }

    loadModels().then(result => result)

    async function getMostConfidentFace(image){
        return await faceapi.detectSingleFace(image)
    }

    function setCropBoundaries(boxCoordinates) {
        const dataX = document.getElementById('dataX')
        const dataY = document.getElementById('dataY')
        const dataWidth = document.getElementById('dataWidth')
        const dataHeight = document.getElementById('dataHeight')
        dataX.value = Math.ceil(boxCoordinates.x)
        dataY.value = Math.ceil(boxCoordinates.y)
        dataWidth.value = Math.ceil(boxCoordinates.width)
        dataHeight.value = Math.ceil(boxCoordinates.height)
    }

    image = document.getElementById('image')
    $('#autodetector').click(function(e) {
        e.preventDefault();
        const canvas = faceapi.createCanvasFromMedia(image)
        const displaySize = { width: image.width, height: image.height }
        getMostConfidentFace(image)
            .then((faceDetection) => {
                const resizedDetection = faceapi.resizeResults(faceDetection, displaySize)
                const cropperSpace = document.getElementById('image-with-cropper')
                const autoDetection = document.getElementById('autodetection')
                cropperSpace.style.display = "none" 
                autoDetection.replaceWith(canvas)
                faceapi.draw.drawDetections(canvas, resizedDetection)
                setCropBoundaries(resizedDetection.box)
            })
            .catch(error => console.log(error))
        });
});