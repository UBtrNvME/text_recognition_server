window.addEventListener("load", () => {
    let data_div = document.getElementById("data")

    var bboxes = JSON.parse(data_div.dataset.boxes)
    // let images = JSON.parse(data_div.dataset.images)
    // var svg = generateBoundingBoxes(bboxes, doc)
    // container.appendChild(svg)
    // document.getElementsByTagName('button')[0].onclick = toggleText
    // generateNotebookContents(images, bboxes)
    mapNotebookContentsWithSVG(bboxes)
});

const generateBoundingBoxes = (boxes, image) => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", image.width)
    svg.setAttribute("height", image.height)
    boxes.forEach((group) => {
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", "row")
        group.forEach((row) => {
            const c = document.createElementNS("http://www.w3.org/2000/svg", "g")
            c.setAttribute("class", "col")
            row.forEach((col) => {
                let rectSVG = createSVGRectangle(col)
                c.appendChild(rectSVG)
            })
            g.appendChild(c)
        })
        svg.appendChild(g)
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

// function toggleText() {
//     let rawText = document.getElementsByClassName("raw-text-container")[0]
//     rawText.innerHTML = generateText()
//     rawText.classList.toggle("hide")
//     document.getElementsByClassName("container")[0].classList.toggle("hide")
// }

function generateText(svg) {
    let arr = []
    svg.childNodes.forEach(row => {
        let r = []
        row.childNodes.forEach(col => {
            let c = []
            col.childNodes.forEach(e => {
                c.push(e.lastChild.innerHTML);
            })
            r.push(`<span>${c.join("\n")}</span>`);
        })
        arr.push(`<div>${r.join("\n")}</div>`)
    })
    return arr.join("\n")
}

// function generateTextContainer(svg, index) {
//     const text = generateText(svg)
//     const textContainer = document.createElement("div")
//     textContainer.setAttribute("class", "notebook__page-text hidden")
//     textContainer.setAttribute("id", `notebook__page-text_${index}`)
//     textContainer.innerHTML = text
//     return textContainer
// }

// function generateButton(image_container, text_container) {
//     const button = document.createElement("button")
//     button.innerText = "Toggle"
//     button.onclick = () => {
//         image_container.classList.toggle("hide")
//         text_container.classList.toggle("hide")
//     }
//     return button
// }

// function generateNotebookContents(images, boxes) {
//     const notebookContent = document.getElementsByClassName("notebook-content")[0]
//     for (let i = 0; i < images.length; i++) {
//         const page = document.createElement("div")
//         page.setAttribute("class", "notebook__page")
//         page.setAttribute("id", `notebook__page_${i + 1}`)
//         const imageContainer = document.createElement("div")
//         imageContainer.setAttribute("class", "notebook__page-image")
//         imageContainer.setAttribute("id", `notebook__page-image_${i + 1}`)
//         const image = document.createElement("img")
//         image.setAttribute("src", images[i])
//         const svg = generateBoundingBoxes(boxes["Document"][`page_${i + 1}`], images[i])
//         const text = generateTextContainer(svg, i + 1)
//         const button = generateButton(imageContainer, text)
//         imageContainer.appendChild(image)
//         imageContainer.appendChild(svg)
//         page.appendChild(button)
//         page.appendChild(imageContainer)
//         page.appendChild(text)
//         notebookContent.appendChild(page)
//     }
// }

function mapNotebookContentsWithSVG(bboxes) {
    const pages = document.getElementsByClassName("notebook__page")
    for (let i = 0; i < pages.length; i++) {
        const page = pages[i]
        const imageContainer = page.getElementsByClassName("notebook__page-image")[0]
        console.log(bboxes["Document"][`page_${i + 1}`])
        const svg = generateBoundingBoxes(bboxes["Document"][`page_${i + 1}`], imageContainer.children[0])
        const text = page.getElementsByClassName("notebook__page-text")
        text.innerHTML = generateText(svg)
        imageContainer.appendChild(svg)
        page.getElementsByTagName("button")[0].onclick = () => {
            console.log(`button ${i}`)
            imageContainer.classList.toggle("hide")
            text.classList.toggle("hide")
        }
    }
}
