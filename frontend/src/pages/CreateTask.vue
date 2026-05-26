<template>
    <div class="task-overlay" @click.self="$emit('close')">
        <div class="task-modal">

            <div class="task-header">
                <h2>📋 Создание задачи</h2>

                <button class="close-btn" @click="$emit('close')">
                    ✖
                </button>
            </div>

            <div class="task-body">

                <input v-model="form.title" placeholder="Название задачи" />

                <textarea v-model="form.description" placeholder="Описание" />

                <label>
                    Срок:
                </label>

                <input type="datetime-local" v-model="form.deadline" />

                <label>
                    Чек-лист
                </label>

                <div v-for="(item, index) in form.checklist" :key="index" class="check-item">
                    <input v-model="form.checklist[index]" placeholder="Пункт" />

                    <button @click="removeCheck(index)">
                        ✖
                    </button>
                </div>

                <button class="add-check" @click="addCheck">
                    + добавить пункт
                </button>


                <label>
                    Файл
                </label>

                <input type="file" @change="selectFile" />


            </div>

            <div class="task-footer">

                <button class="save-btn" @click="createTask">
                    Создать
                </button>

            </div>

        </div>
    </div>
</template>

<script setup>

import { ref } from "vue"
import axios from "axios"

const emit = defineEmits([
    "close",
    "created"
])

const props = defineProps({
    chatId: Number
})

const form = ref({
    title: "",
    description: "",
    deadline: "",
    checklist: []
})

const file = ref(null)

const addCheck = () => {

    form.value.checklist.push("")

}

const removeCheck = (index) => {

    form.value.checklist.splice(index, 1)

}

const selectFile = (e) => {

    file.value = e.target.files[0]

}

const createTask = async () => {

    try {

        const token = localStorage.getItem("token")

        const formData = new FormData()

        formData.append(
            "title",
            form.value.title
        )

        formData.append(
            "description",
            form.value.description
        )

        formData.append(
            "deadline",
            form.value.deadline
        )

        formData.append(
            "chat_id",
            props.chatId
        )

        formData.append(
            "checklist",
            JSON.stringify(
                form.value.checklist
            )
        )

        if (file.value) {

            formData.append(
                "file",
                file.value
            )

        }

        await axios.post(
            "http://127.0.0.1:8000/create-task",
            formData,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        )

        alert("Задача создана")

        emit("created")

        emit("close")

    }
    catch (e) {

        console.log(e)

        alert("Ошибка")

    }

}

</script>

<style scoped>

.task-overlay{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.8);
    backdrop-filter:blur(8px);

    display:flex;
    align-items:center;
    justify-content:center;

    z-index:99999;

    animation:fadeIn .25s ease;
}

.task-modal{

    width:750px;
    max-height:90vh;

    overflow-y:auto;

    background:
    linear-gradient(
    135deg,
    rgba(102,126,234,.95),
    rgba(118,75,162,.95)
    );

    border-radius:25px;

    box-shadow:
    0 15px 50px rgba(0,0,0,.4);

    backdrop-filter:blur(25px);

    border:1px solid
    rgba(255,255,255,.15);

    color:white;

    padding:25px;

    animation:zoom .25s ease;
}

.task-header{

    display:flex;
    justify-content:space-between;
    align-items:center;

    margin-bottom:25px;
}

.task-header h2{

    margin:0;

    font-size:24px;
}

.close-btn{

    width:40px;
    height:40px;

    border:none;

    border-radius:50%;

    background:
    rgba(255,255,255,.1);

    color:white;

    cursor:pointer;

    font-size:18px;

    transition:.2s;
}

.close-btn:hover{

    background:
    rgba(255,255,255,.25);

    transform:rotate(90deg);

}

.task-body{

    display:flex;
    flex-direction:column;

    gap:16px;
}

.task-body label{

    font-size:13px;

    opacity:.8;

    margin-top:10px;
}

.task-body input,
.task-body textarea{

    border:none;

    padding:14px 18px;

    border-radius:14px;

    background:
    rgba(255,255,255,.12);

    color:white;

    outline:none;

    font-size:14px;

    transition:.2s;

    backdrop-filter:blur(10px);
}

.task-body input::placeholder,
.task-body textarea::placeholder{

    color:
    rgba(255,255,255,.5);

}

.task-body input:focus,
.task-body textarea:focus{

    background:
    rgba(255,255,255,.2);

    box-shadow:
    0 0 0 3px
    rgba(255,255,255,.15);

}

.task-body textarea{

    resize:none;

    min-height:120px;
}

.check-item{

    display:flex;
    gap:10px;

    align-items:center;
}

.check-item input{

    flex:1;
}

.check-item button{

    width:42px;
    height:42px;

    border:none;

    border-radius:12px;

    background:#e74c3c;

    color:white;

    cursor:pointer;

    transition:.2s;
}

.check-item button:hover{

    background:#c0392b;

    transform:scale(.95);

}

.add-check{

    background:
    rgba(255,255,255,.12);

    border:none;

    color:white;

    padding:14px;

    border-radius:14px;

    cursor:pointer;

    transition:.2s;
}

.add-check:hover{

    background:
    rgba(255,255,255,.2);

}

.task-footer{

    margin-top:30px;

    display:flex;

    justify-content:flex-end;

    gap:10px;
}

.save-btn{

    padding:14px 30px;

    border:none;

    border-radius:14px;

    background:
    linear-gradient(
    135deg,
    #667eea,
    #764ba2
    );

    color:white;

    font-size:15px;

    font-weight:600;

    cursor:pointer;

    transition:.25s;
}

.save-btn:hover{

    transform:translateY(-2px);

    box-shadow:
    0 10px 25px
    rgba(0,0,0,.3);

}

.save-btn:active{

    transform:scale(.97);

}

input[type=file]{

padding:12px;

cursor:pointer;

}

input[type=file]::file-selector-button{

background:#667eea;

border:none;

padding:10px 15px;

border-radius:10px;

color:white;

margin-right:10px;

cursor:pointer;
}


.task-modal::-webkit-scrollbar{

width:6px;

}

.task-modal::-webkit-scrollbar-track{

background:
rgba(255,255,255,.08);

border-radius:10px;

}

.task-modal::-webkit-scrollbar-thumb{

background:
rgba(255,255,255,.25);

border-radius:10px;

}

@keyframes fadeIn{

from{
opacity:0;
}

to{
opacity:1;
}

}

@keyframes zoom{

from{

opacity:0;

transform:
scale(.9);

}

to{

opacity:1;

transform:
scale(1);

}

}


@media(max-width:768px){

.task-modal{

width:95%;

padding:20px;

}

.task-header h2{

font-size:18px;

}

}

</style>