import { useState } from "react";
import axios from "axios";
import { BounceLoader } from "react-spinners";
import ReactMarkdown from "react-markdown";

import { API_BASE_URL, WEBSOCKET_URL } from "../../config";

const api = axios.create({
  baseURL: API_BASE_URL,
});

const Expander = ({ title, content, source }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="border-2 border-blue-500 p-3 mb-3 rounded-md">
      <b onClick={() => setIsOpen(!isOpen)} className="cursor-pointer p-3 mb-2">
        {title}
      </b>
      {isOpen && <p className="p-3 text-left">{content}</p>}
      {isOpen && (
        <p className="p-3 text-left">
          Source:{" "}
          <a
            href={source}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500"
          >
            {source}
          </a>
        </p>
      )}
    </div>
  );
};

function QuestionForm() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    setAnswer("");
    setIsLoading(true);
    e.preventDefault();

    const websocket = new WebSocket(WEBSOCKET_URL);

    websocket.onopen = () => {
      websocket.send(question);
    };

    websocket.onmessage = (event) => {
      console.log("Received event: ", event.data);
      const data = JSON.parse(event.data);
      if (data.event_type == "on_retriever_end") {
        setDocuments(data.content);
      } else if (data.event_type == "on_chat_model_stream") {
        setAnswer((prev) => prev + data.content);
      }
    };

    websocket.onclose = (event) => {
      setIsLoading(false);
    };
  };

  const handleIndexing = async (e) => {
    e.preventDefault();
    setAnswer("");
    setIsLoading(true);
    const response = await api.post("/indexing", { message: question });
    setAnswer(response.data.response);
    setIsLoading(false);
  };

  return (
    <div className="w-11/12 mx-auto flex flex-col items-center">
      <form className="w-1/2 flex flex-col items-center gap-2">
        <input
          className="w-full p-3 text-xl border border-gray-300 rounded-lg shadow-sm text-center bg-white text-black"
          type="text"
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value);
          }}
        />

        <div className="flex gap-2">
          <button
            className="p-3 mt-4 font-medium rounded-lg bg-blue-500 text-white shadow-sm"
            type="submit"
            onClick={handleSubmit}
          >
            Q&A
          </button>
          <button
            className="p-3 mt-4 font-medium rounded-lg bg-red-500 text-white shadow-sm"
            type="submit"
            onClick={handleIndexing}
          >
            Index
          </button>
        </div>
      </form>
      {isLoading && (
        <div className="mt-3">
          <BounceLoader color="#3498db" />
        </div>
      )}
      {answer && (
        <div className="flex justify-around items-start gap-5 w-full">
          <div className="w-1/2 text-xl">
            <h2 className="font-bold">Answer:</h2>
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
          <div className="w-1/2 text-xl">
            <h2 className="font-bold">Documents:</h2>
            <ul>
              {documents.map((doc, index) => (
                <Expander
                  key={index}
                  title={
                    doc.page_content.split(" ").slice(0, 5).join(" ") + "..."
                  }
                  content={doc.page_content}
                  source={doc.metadata.source_url}
                />
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuestionForm;
