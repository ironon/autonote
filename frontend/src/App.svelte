<script lang="ts">
  let gpt4 = false
  let generated = false
  let inputType = "slideshow"
  let wantsStudyGuide = true
  let wantsAnkiCSV = true
  let wantsMarkdownNotes = true  
  // let wantsAIStitching = false 
  function goTo(e, path:string) {
    e.preventDefault()
    window.open(path)
  }
  function uploadFile() {
    var fileInput = document.getElementById('pdf-file');
    var file = fileInput.files[0];
    var formData = new FormData();
    formData.append(file.name, file);
    formData.append("inputType", inputType)

    generated = false
    fetch(`/sendnotes?inputType=${inputType}&gptfour=${gpt4.toString()}&wantsStudyGuide=${wantsStudyGuide.toString()}&wantsAnkiCSV=${wantsAnkiCSV.toString()}&wantsMarkdownNotes=${wantsMarkdownNotes.toString()}`, {
      method: 'POST',
      body: formData,
      headers: {
        credentials: 'include',
        Authorization: 'tNo6QG1VQ7Oc1nm14k6-gKqORXyJe3kOYeDGyoRvKGE',
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      console.log('File uploaded successfully');
      return response.json()
    }).then(questions => {
      console.log(questions)
      generated = true
      //@ts-ignore
      window.questions = questions
    })
    .catch(error => {
      console.error('Error uploading file:', error);
    });
       //@ts-ignore
    fileInput.value = null
  }
</script>


<div id="app2">

  <h1 id="title">THE AUTO-STUDY 3000</h1>
  <form id="formthing">
    <label for="pdf-file">Select a PDF file to upload:</label>
    <input type="file" id="pdf-file" name="pdf-file" accept=".pdf">
    <br>
    <button type="button" on:click={uploadFile}>Upload</button>
    <div id="settings">
      <span>Use GPT-4? </span>
      <input type="checkbox" bind:checked={gpt4}/>
      <br/>
      <span>Note Type</span>
      <select bind:value={inputType}>
        <option value="slideshow">PDF (Slideshow)</option>
        <option value="pdf">PDF</option>
        <option value="markdown">Markdown Notes</option>
      </select>
    </div>
    {#if generated}
    
    <div id="output">
      <h2>Output</h2>
      <!-- <span>Study Guide </span>
      <input type="checkbox" bind:checked={wantsStudyGuide}/>
      <br/> -->
      <button id="output-button" on:click={(e) => goTo(e, window.questions.markdown_pdf)}>
        <p>Study Guide</p>
        <img src="/file-text.svg" alt="" />
      </button>
      <button id="output-button" on:click={(e) => goTo(e, window.questions.markdown)}>
        <p>Markdown</p>
        <img src="/scroll-text.svg" alt=""/>
      </button>
      <button id="output-button" on:click={(e) => goTo(e, window.questions.anki)}>
        <p>Questions (Anki)</p>
        <img src="/copy-check.svg" alt=""/>
      </button>
      <button id="output-button" on:click={(e) => goTo(e,window.questions.csv)}>
        <p>Questions (CSV)</p>
        <img src="/scroll-text.svg" alt=""/>
      </button>
    </div>
    {/if}
  </form>
  
</div>
<style>


body {
  background: linear-gradient(to bottom right, #0077C2, #005EBD, #0042B7, #002DAF, #001FAB);
  /* Replace the color codes with the desired shades of blue */
  margin: 0;
  padding: 0;
}

#output-button {
  width: 9rem;
  height: 9rem;
  padding: 0.5rem;
}
#app2 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  /* The above code centers the container vertically and horizontally */
  text-align: center;
}

#settings {
  margin-top: 1rem;
}
form {
  background-color: #FFFFFF;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  /* The above code styles the form with a white background, rounded corners, and a box shadow */
}

#title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 10px;
}

input[type=file] {
  display: block;
  margin-bottom: 20px;
}
#output {
  margin-top: 1rem;
}
button {
  background-color: #0077C2;
  color: #FFFFFF;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #005EBD;
}

button:active {
  background-color: #0042B7;
}


</style>
