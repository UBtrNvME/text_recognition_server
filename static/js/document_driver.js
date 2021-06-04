window.addEventListener("load", () => {
    let doc = document.getElementById("doc");
    let container = document.getElementsByClassName("container")[0]
    let data_div = document.getElementById("data")
    let text = document.getElementById("data2").dataset.text
    console.log(text)
    document.getElementsByClassName("raw-text-container")[0].innerHTML = text
    let bboxes = JSON.parse(data_div.dataset.boxes)
    svg = generateBoundingBoxes(bboxes, doc)
    container.appendChild(svg)
    document.getElementsByTagName('button')[0].onclick = toggleText
});

const generateBoundingBoxes = (boxes, image) => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", image.width)
    svg.setAttribute("height", image.height)
    boxes.forEach((box) => {
        let rectSVG = createSVGRectangle(box)
        svg.appendChild(rectSVG)
    })
    let rect = image.getBoundingClientRect();
    // svg.setAttribute("style", `position: absolute; top:${rect.top}px; left:${rect.left}px`)
    svg.setAttribute("class", `stack-top`)
    // svg.setAttribute("style", `float: left; margin-right: -100%; position: relative;`)
    return svg
};

const createSVGRectangle = (box) => {
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", box[0])
    rect.setAttribute("y", box[1])
    rect.setAttribute("width", box[2])
    rect.setAttribute("height", box[3])
    rect.setAttribute("style", `fill-opacity: 0.05;`)
    rect.setAttribute("class", "valid")
    rect.addEventListener("click", (e) => {
        if (e.target.classList) {
            e.target.classList.toggle("valid")
            e.target.classList.toggle("invalid")
        }
    })
    rect.innerHTML = `<title>${box[4]}</title>`
    return rect

}

function toggleText() {
    document.getElementsByClassName("raw-text-container")[0].classList.toggle("hide")
    document.getElementsByClassName("container")[0].classList.toggle("hide")
}
