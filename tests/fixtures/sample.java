public class SampleApp {
    private String name;
    private int counter;

    public SampleApp(String name) {
        this.name = name;
        this.counter = 0;
    }

    public int process(int value) {
        if (value > 0) {
            for (int i = 0; i < value; i++) {
                if (i % 2 == 0) {
                    counter += i;
                } else if (i % 3 == 0) {
                    counter += i * 2;
                }
            }
        }
        return counter;
    }

    public void resetCounter() {
        counter = 0;
        System.out.println("Counter reset for " + name);
    }

    public static void main(String[] args) {
        SampleApp app = new SampleApp("test");
        int result = app.process(10);
        System.out.println("Result: " + result);
    }
}
