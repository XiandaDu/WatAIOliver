export const recordAudio = (function() {
  const func = async function recordAudio(stream) {
    try {
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      })
      const audioChunks = []

      return new Promise((resolve, reject) => {
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data)
          }
        }

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/webm" })
          resolve(audioBlob)
        }

        mediaRecorder.onerror = () => {
          reject(new Error("MediaRecorder error occurred"))
        }

        mediaRecorder.start(1000)
        ;(func).currentRecorder = mediaRecorder
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred"
      throw new Error("Failed to start recording: " + errorMessage)
    }
  }

  ;(func).stop = () => {
    const recorder = (func).currentRecorder
    if (recorder && recorder.state !== "inactive") {
      recorder.stop()
    }
    delete (func).currentRecorder
  }

  return func;
})()
