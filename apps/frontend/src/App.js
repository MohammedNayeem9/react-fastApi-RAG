import logo from "./logo.svg";
import "./index.css";
import "./App.css";

import QuestionForm from "./components/home/QuestionForm";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>Welcome to Fullstack-RAG!</p>
        <QuestionForm />
      </header>
    </div>
  );
}

export default App;
