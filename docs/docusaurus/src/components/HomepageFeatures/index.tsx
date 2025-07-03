import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Modular and Extensible Architecture',
    Svg: require('@site/static/img/data.svg').default,
    description: (
      <>
        Building Intelligence is designed with a flexible, three-layered architecture that separates device communication, data management, and control logic. This allows developers to easily build and deploy custom grid services using a powerful REST API without modifying the core platform.
      </>
    ),
  },
  {
    title: 'Advanced Data Processing and Forecasting',
    Svg: require('@site/static/img/data1.svg').default,
    description: (
      <>
        Go beyond simple data collection. Our Data Engine uses machine learning to forecast energy consumption and generation, continuously improving its models. With robust data handling using InfluxDB and Redis, you can build truly intelligent applications.
      </>
    ),
  },
  {
    title: 'Seamless Southbound and Northbound Integration',
    Svg: require('@site/static/img/snbound.svg').default,
    description: (
      <>
        Connect with a wide range of smart devices using standard protocols like Modbus, Bacnet, and Zigbee, or through our custom Home Assistant interface. The Building Intelligence platform can provide a bridge between your building's devices and cloud-based services, enabling sophisticated energy management solutions.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
