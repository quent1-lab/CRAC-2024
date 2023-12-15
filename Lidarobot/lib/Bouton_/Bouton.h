/*
 * Nom de la bibliothèque : Bouton
 * Auteur : Quent1-lab
 * Date : 22/10/2022
 * Version : 1.0.3
 * 
 * Description : Bibliothèque pour la gestion des boutons.
 * 
 * Cette bibliothèque est un logiciel libre ; vous pouvez la redistribuer et/ou
 * la modifier selon les termes de la Licence Publique Générale GNU telle que publiée
 * par la Free Software Foundation ; soit la version 2 de la Licence, ou
 * (à votre discrétion) toute version ultérieure.
 */



class Bouton{

    public:
        Bouton();

        void begin(int pin,bool type_bt,int delay_click,int delay_press,int delay_rebond);

        bool click();
        bool press();
        void read_Bt();
        int etat();
    
    private:
        bool timer(int delay);
        void reset();  
        int d_read(); 
        void timer_reset();

        int PIN;
        unsigned int TIME_BT;
        bool TYPE;
        int ETAT = 0;

        int DELAY_CLICK;
        int DELAY_PRESS;
        int DELAY_REBOND;
        int DELAY_RESET;
};