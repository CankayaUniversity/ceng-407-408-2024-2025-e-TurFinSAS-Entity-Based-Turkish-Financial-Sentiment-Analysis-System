import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { getAuth, 
         GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAP-VqipBhqQjtuQ7jY5ileVqEkABW6wUA",
  authDomain: "e-turfinsas.firebaseapp.com",
  projectId: "e-turfinsas",
  storageBucket: "e-turfinsas.firebasestorage.app",
  messagingSenderId: "423056230679",
  appId: "1:423056230679:web:9a0ac90086fd52b1398f52",
  measurementId: "G-Z77DEZ0S02"
};

  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const db = getFirestore(app);

export { auth, provider, db };