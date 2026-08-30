import express from 'express';
import { spawn } from 'node:child_process';
const app=express(); app.use(express.json()); app.use(express.static('.'));
let proc=null;
app.post('/api/start',(req,res)=>{if(proc)return res.json({message:'Agent đang chạy'}); const {message,count=1,delay=10}=req.body||{}; if(!message)return res.status(400).json({message:'Thiếu tin nhắn'}); proc=spawn('node',['agent/agent.js'],{env:{...process.env,MESSAGE:message,COUNT:String(count),DELAY:String(delay)}}); proc.on('close',()=>proc=null); res.json({message:'Đã khởi động agent'});});
app.post('/api/stop',(req,res)=>{if(proc){proc.kill('SIGTERM');proc=null;return res.json({message:'Đã dừng agent'});}res.json({message:'Agent không chạy'});});
app.listen(process.env.PORT||3000,'0.0.0.0',()=>console.log('Dashboard listening'));
