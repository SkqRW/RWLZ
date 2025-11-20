Para compilar el lenguaje ejecuta

python src/rwlz.py --compile "archivo_a_compilar"

y luego ejecuta el programa resultante

Y si, el argumento es obligatorio para que produzca el ejecutable.


Los test en la carpetas valid, invalid, semantic no estan verificados para que compilen, debido a que al momento de hacer el LLVM, se decidio usar la funcion main para que sea el centro de la ejecucion del programa, por lo que puedes utilizar los otros ejemplos como:
- lizard.rwlz
- closest_points.rwlz (el mas completo)
- cl.rwlz
- stair.rwlz

esos son los archivos que estan asegurados de compilar.

Para crear nuevos ejemplos, use una sintaxis parecida a C. Que tengas un feliz dia :D