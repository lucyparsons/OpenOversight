$(document).ready(function() {;
    const MODEL_URL = '/static/face_api_js_models'

    async function loadModels(){
        await faceapi.loadFaceRecognitionModel(MODEL_URL)
        await faceapi.loadSsdMobilenetv1Model(MODEL_URL)
        await faceapi.loadFaceLandmarkModel(MODEL_URL)
    }

    loadModels().then(result => result)

    async function getMostConfidentFace(image){
        return await faceapi.detectSingleFace(image).withFaceLandmarks().withFaceDescriptor()
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

    function loadFaceRegistry() {
        labels = ['JasonBellavance', 'BrianDiFranco', 'MichaelHemond']
        return Promise.all(
            labels.map(async label => {
                const descriptions = []
                for (let i = 1; i <= 2; i++) {
                    const img = await faceapi.fetchImage(`/static/images/${label}${i}.jpg`)
                    const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor()
                    descriptions.push(detections.descriptor)
                }
                return new faceapi.LabeledFaceDescriptors(label, descriptions)
            })
        )
    }

    async function identifyFace(detection) {
        const labeledFaceDescriptors = await loadFaceRegistry()

        const faceMatcher = new faceapi.FaceMatcher(labeledFaceDescriptors, 0.6)
        const result = faceMatcher.findBestMatch(detection.descriptor)
        const facialRecogDisplay = document.getElementById('facial-recog-display')
        if (result.label != "unknown") {
            facialRecogDisplay.style.display = "inline-block"
            const officerName = document.getElementById('facial-recog-result')
            officerName.innerText = result.label
        } 
        if (result.label == "unknown") {
            facialRecogDisplay.style.display = "inline-block"
            facialRecogDisplay.innerText = "Facial recognition did not find a match for this officer.  Please search through the roster for a match."
        }
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
                faceapi.draw.drawDetections(canvas, resizedDetection.detection)
                setCropBoundaries(resizedDetection.detection.box)
                document.getElementById('facial-recog-trigger').style.display = "inline-block"
                $('#facial-recog-trigger').click(function(e) {
                    e.preventDefault();
                    identifyFace(resizedDetection)
                })
            })
            .catch(error => console.log(error))
        });
});