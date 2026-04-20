let LANG = {}

async function loadLang(lang){

const res = await fetch("/static/lang/" + lang + ".json")
LANG = await res.json()

document.querySelectorAll("[data-i18n]").forEach(el => {

const key = el.getAttribute("data-i18n")

// 如果存在翻译
if(LANG[key]){
el.innerText = LANG[key]
}
// 如果不存在翻译，保持原文本
else{
console.warn("Missing translation:", key)
}

})

localStorage.setItem("lang", lang)

// 🔥 加这里
if (typeof loadTopModels === "function") loadTopModels()
if (typeof loadArbitrageIndex === "function") loadArbitrageIndex()
if (typeof loadVelocity === "function") loadVelocity()

// 强制关闭语言菜单
const menu = document.getElementById("langDropdown")
if(menu){
menu.style.display = "none"
}

}

function initLang(){

let lang = localStorage.getItem("lang")

if(!lang){

const browser = navigator.language || navigator.userLanguage

if(browser.startsWith("it")){
lang="it"
}
else if(browser.startsWith("zh")){
lang="zh"
}
else if(browser.startsWith("bn")){
lang="bn"
}
else{
lang="en"
}

}

loadLang(lang)

}

window.addEventListener("DOMContentLoaded", initLang)
