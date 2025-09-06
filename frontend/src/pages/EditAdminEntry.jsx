import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DragDropZone } from "@/components/ui/drag-drop-zone";
import { FileList } from "@/components/ui/file-list";
import { CourseSelector } from "@/components/ui/course-selector";
import AdminSidebar from "@/components/AdminSidebar";

export default function EditAdminEntry() {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    name: "",
    notes: "",
    doc: "",
    model: "",
    prompt: "",
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");

  // GET ENTRY DATA HERE
  useEffect(() => {
    if (location.state?.entry) {
      setFormData(location.state.entry);
      // Parse existing document paths if they exist
      if (location.state.entry.doc) {
        const existingDocs = location.state.entry.doc
          .split(",")
          .map((doc) => doc.trim());
        setUploadedFiles(
          existingDocs.map((doc) => ({
            name: doc.split("/").pop(),
            path: doc,
            size: 0,
          }))
        );
      }
    }
  }, [location.state]);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleFilesDrop = async (files) => {
    if (!selectedCourseId) {
      alert("Please select a course first");
      return;
    }

    try {
      // Upload files to RAG system via backend
      const uploadFormData = new FormData();
      uploadFormData.append("course_id", selectedCourseId);
      uploadFormData.append("user_id", "admin");

      for (const file of files) {
        uploadFormData.append("files", file);
      }

      const uploadResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/upload_files_for_rag`,
        {
          method: "POST",
          body: uploadFormData,
          signal: AbortSignal.timeout(300000),
        }
      );

      if (uploadResponse.ok) {
        const uploadData = await uploadResponse.json();
        // console.log("RAG upload completed successfully:", uploadData);

        // Add successfully uploaded files to the UI
        const newFiles = uploadData.results
          .filter((result) => result.status === "completed")
          .map((result) => ({
            name: result.filename,
            size: 0,
            type: result.type,
            path: `/uploads/${result.filename}`,
          }));

        setUploadedFiles((prev) => [...prev, ...newFiles]);

        // Update the doc field with new file paths
        const allPaths = [...uploadedFiles, ...newFiles].map(
          (file) => file.path
        );
        handleInputChange("doc", allPaths.join(","));

        // console.log("Files uploaded to RAG:", newFiles);
      } else {
        console.error(
          "RAG upload failed:",
          uploadResponse.status,
          uploadResponse.statusText
        );
      }
    } catch (error) {
      console.error("Error uploading files to RAG:", error);
    }
  };

  const handleRemoveFile = (index) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);

    // Update the doc field
    const allPaths = newFiles.map((file) => file.path);
    handleInputChange("doc", allPaths.join(","));
  };

  const handleSave = () => {
    // console.log("Saving updated entry:", formData);
    // API CALL HERE TO SAVE CHANGES
    navigate("/admin");
  };

  const handleCancel = () => {
    navigate("/admin");
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar title="Edit Entry" />
      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Edit Entry</h1>
          <div className="flex space-x-3">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg border p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Enter name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <Input
                    id="model"
                    value={formData.model}
                    onChange={(e) => handleInputChange("model", e.target.value)}
                    placeholder="Enter model"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleInputChange("notes", e.target.value)}
                  placeholder="Enter notes"
                  rows={3}
                />
              </div>

              <CourseSelector
                value={selectedCourseId}
                onChange={setSelectedCourseId}
              />

              <div className="space-y-4">
                <Label>Documents</Label>
                <DragDropZone
                  onFilesDrop={handleFilesDrop}
                  acceptedFileTypes={[
                    "pdf",
                    "doc",
                    "docx",
                    "txt",
                    "tex",
                    "md",
                    "json",
                    "csv",
                  ]}
                  multiple={true}
                />
                <FileList
                  files={uploadedFiles}
                  onRemove={handleRemoveFile}
                  className="mt-4"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Textarea
                  id="prompt"
                  value={formData.prompt}
                  onChange={(e) => handleInputChange("prompt", e.target.value)}
                  placeholder="Enter the prompt template"
                  rows={8}
                  className="font-mono text-sm"
                />
                <p className="text-sm text-gray-500">
                  This is the prompt template that will be used for this entry
                </p>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t">
                <Button variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button onClick={handleSave}>Save Changes</Button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
