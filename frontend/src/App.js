import React, { useState } from 'react';
import './App.css';
import config from './config'; // Đảm bảo đường dẫn đúng đến tệp config.js

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [similarImages, setSimilarImages] = useState([]);
  const [displayResults, setDisplayResults] = useState(false);
  const [fileName, setFileName] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('file-input');

    if (fileInput.files.length === 0) {
      alert('Please select an image to upload.');
      return;
    }

    const file = fileInput.files[0];
    console.log("file: ", file)
    setFileName(file.name); // Update file name state when file is selected
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8002/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const results = await response.json();
        const topResults = results.slice(0, 10);
        setSimilarImages(topResults);
        setUploadedImage(URL.createObjectURL(fileInput.files[0]));
        setDisplayResults(true);
      } else {
        alert('Failed to upload image.');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('An error occurred while uploading the image.');
    }
  };

  return (
    <div className="App">
      <h1>Upload an Image</h1>
      <form id="upload-form" onSubmit={handleSubmit} encType="multipart/form-data">
        <input type="file" name="file" id="file-input" required />
        <input type="submit" value="Upload" />
      </form>

      {displayResults && (
        <div id="results">
          <h1>Uploaded Image</h1>
          {uploadedImage && <img id="uploaded-image" src={uploadedImage} alt="Uploaded" style={{ maxWidth: '300px' }} />}
          <p>Type: {fileName}</p>
          
          <h1>Similar Images</h1>
          <div id="similar-images" style={{ display: 'flex', flexWrap: 'wrap' }}>
            {similarImages.map((result, index) => {
              const normalizedPath = result.img_path.replace(/\\/g, '/');
              const basePath = config.IMAGE_PREPROCESSING_PATH;
              if (normalizedPath.includes(basePath)) {
                const relativePath = normalizedPath.split(basePath)[1];
                const imgSrc = `http://127.0.0.1:8002/${relativePath}`;
                // const imgSrc = result.img_path;
                console.log(imgSrc)
                return (
                  <div key={index} className="image-container">
                    <img src={imgSrc} alt="Similar" style={{ maxWidth: '150px' }} />
                    <p>Score: {result.comparison_result.toFixed(2)}</p>
                    <p>Type: {relativePath.split('/')[1]}</p>
                  </div>
                );
              } else {
                console.error(`Invalid img_path: ${result.img_path}`);
                return null;
              }
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;