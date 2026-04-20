async function api(url,options={}){

const token=localStorage.getItem("token")

const headers={
"Content-Type":"application/json",
...options.headers
}

if(token){
headers["Authorization"]="Bearer "+token
}

const res=await fetch(url,{
...options,
headers,
credentials:"include"
})

const data=await res.json()

if(data && data.status==="error"){
console.log("API error:",data)

if(data.message==="not authenticated"){
localStorage.removeItem("token")
window.location="/login"
}

return null
}

return data
}
