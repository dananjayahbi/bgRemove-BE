const express = require("express");
const multer = require("multer");
const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const { v4: uuidv4 } = require("uuid");
const os = require("os");
const cors = require("cors");

const app = express();
const port = 5000;

app.use(cors());
app.use(express.static("Outputs"));

const upload = multer({ dest: "Uploads/" });

const pythonCommand = os.platform() === "win32" ? "python" : "python3";

//..............................................................................................

// Function to clear the contents of the Uploads and Outputs folders
async function clearFolders() {
  const uploadDir = path.join(__dirname, "Uploads");
  const outputDir = path.join(__dirname, "Outputs");

  // Clear the Uploads folder
  try {
    const uploadFiles = await fs.promises.readdir(uploadDir);
    await Promise.all(
      uploadFiles.map((file) =>
        fs.promises.rm(path.join(uploadDir, file), {
          recursive: true,
          force: true,
        })
      )
    );
    console.log('"Uploads" folder cleaned.');
  } catch (err) {
    console.error(`Error clearing Uploads folder: ${err}`);
  }

  // Clear the Outputs folder
  try {
    const outputFiles = await fs.promises.readdir(outputDir);
    await Promise.all(
      outputFiles.map((file) =>
        fs.promises.rm(path.join(outputDir, file), {
          recursive: true,
          force: true,
        })
      )
    );
    console.log('"Outputs" folder cleaned.');
  } catch (err) {
    console.error(`Error clearing Outputs folder: ${err}`);
  }
}

// Set an interval to clear the folders every 5 hours
setInterval(clearFolders, 5 * 60 * 60 * 1000);

//..............................................................................................

// Root route
app.get("/", (req, res) => {
  res.send("Hello world!");
});

app.post("/upload", upload.array("images", 10), (req, res) => {
  const files = req.files;
  const id = uuidv4();
  const uploadDir = path.join(__dirname, "Uploads", id);
  const outputDir = path.join(__dirname, "Outputs", id);

  fs.mkdirSync(uploadDir, { recursive: true });
  fs.mkdirSync(outputDir, { recursive: true });

  const renamedFiles = files.map((file) => {
    const fileExtension = path.extname(file.originalname);
    const newFilename = `${uuidv4()}${fileExtension}`;
    const newFilePath = path.join(uploadDir, newFilename);

    fs.renameSync(file.path, newFilePath);

    return newFilename;
  });

  const command = `${pythonCommand} remove_bg.py "${uploadDir}" "${outputDir}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`exec error: ${error}`);
      return res.status(500).send("Error processing images");
    }

    console.log(stdout);
    res.json({ id, files: renamedFiles });
  });
});

app.get("/status/:id", (req, res) => {
  const id = req.params.id;
  const outputDir = path.join(__dirname, "Outputs", id);

  fs.readdir(outputDir, (err, files) => {
    if (err || files.length === 0) {
      return res.json({ status: "processing" });
    }

    res.json({ status: "completed", files });
  });
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
