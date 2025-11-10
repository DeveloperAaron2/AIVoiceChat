import { Routes } from '@angular/router';
import { ChatbotPageComponent } from './pages/chatbotPage/chatbotPage.component';

export const routes: Routes = [
    {
        path: '',
        component: ChatbotPageComponent
    },
    {
        path: '**',
        redirectTo: ''
    }
];
