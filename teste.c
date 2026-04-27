#include <stdio.h>
int main() {
    float n1, n2, media;
    printf("Nota da primeira prova: ");
    scanf("%f", &n1);
    printf("Nota da segunda prova: ");
    scanf("%f", &n2);

    media = (n1 + n2) / 2;
    printf("Sua média final é: %.2f\n", media);

    if(media >= 7) {
        printf("Aprovado! Partiu adega comemorar!\n");
    } else {
        printf("Ih, vai ter que estudar mais um pouco...\n");
    }

    return 0;
}